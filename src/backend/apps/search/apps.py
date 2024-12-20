"""
Django application configuration for the search module that integrates MeiliSearch and Pinecone
for high-performance full-text and vector similarity search capabilities.

MeiliSearch version: 1.3+
Pinecone version: 2.0+
"""

import logging
from typing import Optional

from django.apps import AppConfig
from django.conf import settings

# Configure module-level logger
logger = logging.getLogger(__name__)

class SearchConfig(AppConfig):
    """
    Django application configuration for search services integrating MeiliSearch and Pinecone.
    Handles initialization, optimization, and monitoring of search capabilities.
    """
    
    # Django application configuration
    name: str = 'apps.search'
    label: str = 'search'
    verbose_name: str = 'Search Services'
    default_auto_field: str = 'django.db.models.BigAutoField'

    # Search service clients
    _meilisearch_client: Optional[object] = None
    _pinecone_client: Optional[object] = None

    def ready(self) -> None:
        """
        Initialize and configure search services when Django starts.
        Sets up MeiliSearch and Pinecone with optimized performance settings.
        
        Configures:
        - Connection pooling
        - Index optimization
        - Cache warming
        - Performance monitoring
        - Error handling
        """
        if settings.TESTING:
            # Skip initialization during testing
            return

        try:
            self._initialize_meilisearch()
            self._initialize_pinecone()
            self._setup_monitoring()
            self._warm_cache()
        except Exception as e:
            logger.error(f"Failed to initialize search services: {str(e)}")
            raise

    def _initialize_meilisearch(self) -> None:
        """
        Initialize MeiliSearch client and configure indexes with optimized settings.
        """
        try:
            import meilisearch
            
            # Initialize client with connection pooling
            self._meilisearch_client = meilisearch.Client(
                settings.MEILISEARCH_URL,
                settings.MEILISEARCH_API_KEY,
                timeout=settings.MEILISEARCH_TIMEOUT,
                max_retries=3
            )

            # Configure course index
            course_index = self._meilisearch_client.index('courses')
            course_index.update_settings({
                'searchableAttributes': [
                    'code',
                    'name',
                    'description',
                    'institution'
                ],
                'filterableAttributes': [
                    'institution_id',
                    'department',
                    'credits',
                    'level'
                ],
                'sortableAttributes': [
                    'code',
                    'credits'
                ],
                'pagination': {
                    'maxTotalHits': 10000
                },
                'typoTolerance': {
                    'enabled': True,
                    'minWordSizeForTypos': {
                        'oneTypo': 4,
                        'twoTypos': 8
                    }
                }
            })

            # Configure requirements index
            requirements_index = self._meilisearch_client.index('requirements')
            requirements_index.update_settings({
                'searchableAttributes': [
                    'major_code',
                    'institution',
                    'description'
                ],
                'filterableAttributes': [
                    'institution_id',
                    'active',
                    'effective_date'
                ],
                'sortableAttributes': [
                    'effective_date',
                    'major_code'
                ],
                'pagination': {
                    'maxTotalHits': 5000
                }
            })

            logger.info("MeiliSearch initialized successfully")

        except Exception as e:
            logger.error(f"MeiliSearch initialization failed: {str(e)}")
            raise

    def _initialize_pinecone(self) -> None:
        """
        Initialize Pinecone client and configure vector search index.
        """
        try:
            import pinecone
            
            # Initialize Pinecone with optimal settings
            pinecone.init(
                api_key=settings.PINECONE_API_KEY,
                environment=settings.PINECONE_ENVIRONMENT
            )

            # Configure index with performance optimizations
            self._pinecone_client = pinecone.Index(
                settings.PINECONE_INDEX_NAME,
                pool_threads=4,  # Connection pooling
                replicas=2,      # High availability
                shards=2,        # Distributed processing
                pod_type='p1.x1' # High performance pods
            )

            logger.info("Pinecone initialized successfully")

        except Exception as e:
            logger.error(f"Pinecone initialization failed: {str(e)}")
            raise

    def _setup_monitoring(self) -> None:
        """
        Configure monitoring and metrics collection for search services.
        """
        try:
            from prometheus_client import Counter, Histogram
            
            # Search latency metrics
            self.search_latency = Histogram(
                'search_request_latency_seconds',
                'Search request latency in seconds',
                ['search_type', 'index']
            )

            # Search error metrics
            self.search_errors = Counter(
                'search_errors_total',
                'Total search errors',
                ['search_type', 'error_type']
            )

            # Cache hit metrics
            self.cache_hits = Counter(
                'search_cache_hits_total',
                'Total search cache hits',
                ['index']
            )

            logger.info("Search monitoring configured successfully")

        except Exception as e:
            logger.error(f"Failed to setup monitoring: {str(e)}")
            raise

    def _warm_cache(self) -> None:
        """
        Perform initial cache warming for frequently accessed search data.
        """
        try:
            # Warm up course index
            self._meilisearch_client.index('courses').search(
                '',
                limit=100,
                offset=0
            )

            # Warm up requirements index
            self._meilisearch_client.index('requirements').search(
                '',
                limit=100,
                offset=0
            )

            # Warm up vector index
            self._pinecone_client.fetch(ids=['popular_vectors'])

            logger.info("Search cache warming completed")

        except Exception as e:
            logger.error(f"Cache warming failed: {str(e)}")
            # Non-critical error, don't raise
            pass