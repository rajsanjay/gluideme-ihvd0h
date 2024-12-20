"""
Pinecone vector database integration module for Transfer Requirements Management System.
Provides high-performance similarity search capabilities with enhanced caching and monitoring.

Version: 1.0
Author: Transfer Requirements Management System Team
"""

# External imports with versions
import pinecone  # v2.2+
import numpy as np  # v1.24+
import logging
import structlog  # v23.1+
import os
from typing import List, Dict, Any, Optional
from threading import Lock
from functools import wraps
from datetime import datetime

# Internal imports
from utils.cache import CacheManager

# Configure structured logging
logger = structlog.get_logger(__name__)

# Environment configuration
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
PINECONE_ENV = os.getenv('PINECONE_ENV', 'us-west1-gcp')
PINECONE_INDEX = os.getenv('PINECONE_INDEX', 'transfer-requirements')
CACHE_TTL = int(os.getenv('VECTOR_CACHE_TTL', 3600))
BATCH_SIZE = int(os.getenv('VECTOR_BATCH_SIZE', 100))

def synchronized(func):
    """Thread-safety decorator for singleton pattern."""
    lock = Lock()
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        with lock:
            return func(*args, **kwargs)
    return wrapper

def monitor_performance(func):
    """Decorator for monitoring Pinecone operations performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        try:
            result = func(*args, **kwargs)
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(
                "pinecone_operation_completed",
                operation=func.__name__,
                duration=duration,
                success=True
            )
            return result
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(
                "pinecone_operation_failed",
                operation=func.__name__,
                duration=duration,
                error=str(e),
                success=False
            )
            raise
    return wrapper

class PineconeClient:
    """
    Singleton class for managing Pinecone vector database operations with enhanced
    caching, monitoring, and error handling capabilities.
    """
    
    _instance = None
    _index = None
    _cache = None

    def __init__(self):
        """
        Private constructor implementing singleton pattern with enhanced initialization.
        Configures Pinecone client, connection pool, and caching layer.
        """
        if not PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY environment variable is required")

        # Initialize Pinecone with configuration
        pinecone.init(
            api_key=PINECONE_API_KEY,
            environment=PINECONE_ENV
        )

        # Initialize index with connection pooling
        self._index = pinecone.Index(
            PINECONE_INDEX,
            pool_threads=10  # Configurable connection pool
        )

        # Initialize cache manager with encryption
        self._cache = CacheManager(
            enable_encryption=True,
            default_timeout=CACHE_TTL
        )

        logger.info(
            "pinecone_client_initialized",
            environment=PINECONE_ENV,
            index=PINECONE_INDEX
        )

    @classmethod
    @synchronized
    def get_instance(cls) -> 'PineconeClient':
        """
        Get or create thread-safe singleton instance.

        Returns:
            PineconeClient: Singleton instance with configured services
        """
        if cls._instance is None:
            cls._instance = PineconeClient()
        return cls._instance

    @monitor_performance
    def upsert_vectors(
        self,
        vectors: List[np.ndarray],
        ids: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Insert or update vectors with batch processing and monitoring.

        Args:
            vectors: List of numpy arrays representing vectors
            ids: List of unique identifiers for vectors
            metadata: Optional metadata for vectors

        Returns:
            bool: Operation success status
        """
        if len(vectors) != len(ids):
            raise ValueError("Number of vectors must match number of IDs")

        try:
            # Process vectors in configurable batches
            for i in range(0, len(vectors), BATCH_SIZE):
                batch_vectors = vectors[i:i + BATCH_SIZE]
                batch_ids = ids[i:i + BATCH_SIZE]
                batch_metadata = metadata[i:i + BATCH_SIZE] if metadata else None

                # Convert vectors to list format required by Pinecone
                vector_data = [
                    (id, vec.tolist(), meta)
                    for id, vec, meta in zip(
                        batch_ids,
                        batch_vectors,
                        batch_metadata or [None] * len(batch_vectors)
                    )
                ]

                self._index.upsert(vectors=vector_data)

            # Invalidate affected cache entries
            cache_key = self._cache.generate_cache_key("vector_search")
            self._cache.invalidate(cache_key)

            logger.info(
                "vectors_upserted",
                count=len(vectors),
                batch_size=BATCH_SIZE
            )
            return True

        except Exception as e:
            logger.error(
                "vector_upsert_failed",
                error=str(e),
                vector_count=len(vectors)
            )
            raise

    @monitor_performance
    def query_vectors(
        self,
        query_vector: np.ndarray,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """
        Query similar vectors with caching and performance optimization.

        Args:
            query_vector: Numpy array representing query vector
            top_k: Number of similar vectors to return
            filters: Optional filters for query

        Returns:
            List[Dict]: Similar vectors with scores and metadata
        """
        # Generate cache key based on query parameters
        cache_key = self._cache.generate_cache_key(
            "vector_search",
            query_vector.tobytes(),
            top_k,
            filters
        )

        # Try to get results from cache
        cached_results = self._cache.get(cache_key, decrypt=True)
        if cached_results is not None:
            logger.info("vector_search_cache_hit", cache_key=cache_key)
            return cached_results

        try:
            # Query Pinecone
            query_response = self._index.query(
                vector=query_vector.tolist(),
                top_k=top_k,
                filter=filters,
                include_metadata=True
            )

            # Process and format results
            results = [
                {
                    'id': match.id,
                    'score': float(match.score),
                    'metadata': match.metadata
                }
                for match in query_response.matches
            ]

            # Cache results with encryption
            self._cache.set(
                cache_key,
                results,
                timeout=CACHE_TTL,
                encrypt=True
            )

            logger.info(
                "vector_search_completed",
                results_count=len(results),
                top_k=top_k
            )
            return results

        except Exception as e:
            logger.error(
                "vector_search_failed",
                error=str(e),
                top_k=top_k
            )
            raise

    @monitor_performance
    def delete_vectors(self, ids: List[str]) -> bool:
        """
        Delete vectors with cache invalidation.

        Args:
            ids: List of vector IDs to delete

        Returns:
            bool: Operation success status
        """
        try:
            # Process deletion in batches
            for i in range(0, len(ids), BATCH_SIZE):
                batch_ids = ids[i:i + BATCH_SIZE]
                self._index.delete(ids=batch_ids)

            # Invalidate affected cache entries
            cache_key = self._cache.generate_cache_key("vector_search")
            self._cache.invalidate(cache_key)

            logger.info(
                "vectors_deleted",
                count=len(ids),
                batch_size=BATCH_SIZE
            )
            return True

        except Exception as e:
            logger.error(
                "vector_deletion_failed",
                error=str(e),
                id_count=len(ids)
            )
            raise

# Export public interface
__all__ = ['PineconeClient']