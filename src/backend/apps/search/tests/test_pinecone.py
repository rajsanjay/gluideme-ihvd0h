"""
Unit test suite for Pinecone vector database integration.
Tests vector similarity search operations, caching behavior, error handling, and performance benchmarks.

Version: 1.0
Author: Transfer Requirements Management System Team
"""

# External imports with versions
import pytest  # v7.3+
from unittest.mock import Mock, patch  # Python 3.11+
import numpy as np  # v1.24+
import threading  # Python 3.11+
import time  # Python 3.11+
import statistics  # Python 3.11+
from typing import List, Dict

# Internal imports
from apps.search.pinecone import PineconeClient
from utils.cache import CacheManager

# Test constants
TEST_VECTORS_DIMENSION = 768
TEST_BATCH_SIZE = 100
PERFORMANCE_ITERATIONS = 1000
WARMUP_CYCLES = 100
MAX_LATENCY_MS = 200

class TestPineconeClient:
    """
    Comprehensive test suite for PineconeClient class functionality including
    thread safety, cache consistency, and performance benchmarks.
    """

    @pytest.fixture(autouse=True)
    def setUp(self):
        """Set up test environment and fixtures with mock configurations."""
        # Initialize test vectors
        self.test_vectors = np.random.rand(TEST_BATCH_SIZE, TEST_VECTORS_DIMENSION)
        self.test_ids = [f"test_id_{i}" for i in range(TEST_BATCH_SIZE)]
        
        # Mock cache manager
        self.mock_cache = Mock(spec=CacheManager)
        self.mock_cache.get.return_value = None
        
        # Mock Pinecone responses
        self.mock_responses = {
            'query': {
                'matches': [
                    {'id': 'test_id_1', 'score': 0.95, 'metadata': {'field': 'value'}},
                    {'id': 'test_id_2', 'score': 0.85, 'metadata': {'field': 'value'}}
                ]
            }
        }
        
        # Apply patches
        self.patches = [
            patch('apps.search.pinecone.CacheManager', return_value=self.mock_cache),
            patch('pinecone.Index'),
            patch('pinecone.init')
        ]
        for p in self.patches:
            p.start()
            
        # Reset singleton instance
        PineconeClient._instance = None
        
    def tearDown(self):
        """Clean up patches and mocks after tests."""
        for p in self.patches:
            p.stop()

    def test_singleton_pattern(self):
        """Test singleton pattern implementation with thread safety."""
        def get_instance():
            return PineconeClient.get_instance()
        
        # Create multiple threads requesting client instance
        threads = []
        instances = []
        for _ in range(10):
            thread = threading.Thread(target=lambda: instances.append(get_instance()))
            threads.append(thread)
            thread.start()
            
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
            
        # Verify singleton behavior
        assert len(set(id(instance) for instance in instances)) == 1
        assert all(isinstance(instance, PineconeClient) for instance in instances)

    def test_upsert_vectors(self):
        """Test vector insertion/update functionality with batch processing."""
        client = PineconeClient.get_instance()
        
        # Test batch processing
        with patch.object(client._index, 'upsert') as mock_upsert:
            result = client.upsert_vectors(
                vectors=self.test_vectors,
                ids=self.test_ids,
                metadata=[{'field': 'value'} for _ in range(TEST_BATCH_SIZE)]
            )
            
            assert result is True
            assert mock_upsert.call_count == 1
            
            # Verify cache invalidation
            self.mock_cache.invalidate.assert_called_once()
            
        # Test error handling
        with pytest.raises(ValueError):
            client.upsert_vectors(
                vectors=self.test_vectors,
                ids=self.test_ids[:-1]  # Mismatched lengths
            )

    def test_query_vectors(self):
        """Test vector similarity search with comprehensive cache testing."""
        client = PineconeClient.get_instance()
        query_vector = np.random.rand(TEST_VECTORS_DIMENSION)
        
        # Test cache miss scenario
        with patch.object(client._index, 'query') as mock_query:
            mock_query.return_value = Mock(**self.mock_responses['query'])
            
            results = client.query_vectors(
                query_vector=query_vector,
                top_k=2,
                filters={'field': 'value'}
            )
            
            assert len(results) == 2
            assert all('id' in result for result in results)
            assert all('score' in result for result in results)
            assert all('metadata' in result for result in results)
            
            # Verify cache operations
            self.mock_cache.get.assert_called_once()
            self.mock_cache.set.assert_called_once()
            
        # Test cache hit scenario
        self.mock_cache.get.return_value = self.mock_responses['query']['matches']
        results = client.query_vectors(query_vector=query_vector)
        assert len(results) == 2
        mock_query.assert_called_once()

    def test_delete_vectors(self):
        """Test vector deletion functionality and cache invalidation."""
        client = PineconeClient.get_instance()
        
        # Test batch deletion
        with patch.object(client._index, 'delete') as mock_delete:
            result = client.delete_vectors(ids=self.test_ids)
            
            assert result is True
            assert mock_delete.call_count == 1
            
            # Verify cache invalidation
            self.mock_cache.invalidate.assert_called_once()
            
        # Test empty deletion
        with pytest.raises(ValueError):
            client.delete_vectors(ids=[])

    def test_error_handling(self):
        """Comprehensive error handling and recovery testing."""
        client = PineconeClient.get_instance()
        
        # Test API timeout
        with patch.object(client._index, 'query', side_effect=TimeoutError):
            with pytest.raises(TimeoutError):
                client.query_vectors(np.random.rand(TEST_VECTORS_DIMENSION))
        
        # Test invalid dimensions
        with pytest.raises(ValueError):
            client.query_vectors(np.random.rand(TEST_VECTORS_DIMENSION + 1))
            
        # Test connection error recovery
        with patch.object(client._index, 'query', side_effect=[ConnectionError, self.mock_responses['query']]):
            with pytest.raises(ConnectionError):
                client.query_vectors(np.random.rand(TEST_VECTORS_DIMENSION))

    def test_performance(self):
        """Detailed performance benchmarking with statistical analysis."""
        client = PineconeClient.get_instance()
        query_vector = np.random.rand(TEST_VECTORS_DIMENSION)
        
        # Warm-up cycles
        for _ in range(WARMUP_CYCLES):
            with patch.object(client._index, 'query') as mock_query:
                mock_query.return_value = Mock(**self.mock_responses['query'])
                client.query_vectors(query_vector)
        
        # Performance measurement
        latencies = []
        for _ in range(PERFORMANCE_ITERATIONS):
            start_time = time.time()
            with patch.object(client._index, 'query') as mock_query:
                mock_query.return_value = Mock(**self.mock_responses['query'])
                client.query_vectors(query_vector)
            latencies.append((time.time() - start_time) * 1000)  # Convert to ms
            
        # Statistical analysis
        avg_latency = statistics.mean(latencies)
        p95_latency = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
        
        # Verify performance requirements
        assert avg_latency < MAX_LATENCY_MS, f"Average latency {avg_latency}ms exceeds {MAX_LATENCY_MS}ms requirement"
        assert p95_latency < MAX_LATENCY_MS * 1.5, f"95th percentile latency {p95_latency}ms exceeds threshold"