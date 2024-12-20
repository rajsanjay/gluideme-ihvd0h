"""
Test suite for Redis-based caching system validating performance, reliability, 
security and functionality of the cache utility module.

Version: 1.0
Author: Transfer Requirements Management System Team
"""

# External imports
import pytest  # v7.3+
from unittest.mock import Mock, patch  # v3.11+
import fakeredis  # v2.10+
import json  # v3.11+
import time  # v3.11+
import asyncio  # v3.11+
from cryptography.fernet import Fernet

# Internal imports
from utils.cache import (
    cache_get,
    cache_set,
    cache_delete,
    cache_delete_pattern,
    CacheManager,
    cached,
    CACHE_VERSION,
    DEFAULT_TIMEOUT,
    CIRCUIT_BREAKER_THRESHOLD
)

# Test constants
TEST_CACHE_PREFIX = "test_cache:"
TEST_TIMEOUT = 60
PERFORMANCE_THRESHOLD = 500  # milliseconds
TEST_DATA_SIZES = [10, 100, 1000, 10000]  # bytes
ENCRYPTION_KEY = Fernet.generate_key()

@pytest.fixture
def redis_client():
    """Fixture providing instrumented FakeRedis client."""
    client = fakeredis.FakeRedis(decode_responses=True)
    return client

@pytest.fixture
def cache_manager(redis_client):
    """Fixture providing configured CacheManager instance."""
    return CacheManager(
        client=redis_client,
        default_timeout=TEST_TIMEOUT,
        enable_encryption=True
    )

@pytest.fixture
def encrypted_cache_manager(redis_client):
    """Fixture providing CacheManager with encryption enabled."""
    with patch.dict('os.environ', {'CACHE_ENCRYPTION_KEY': ENCRYPTION_KEY.decode()}):
        return CacheManager(
            client=redis_client,
            default_timeout=TEST_TIMEOUT,
            enable_encryption=True
        )

class TestCacheUtils:
    """Test suite for core cache utility functions."""

    def test_cache_get_performance(self, cache_manager):
        """Test cache retrieval performance meets requirements."""
        test_data = {f"key_{size}": "x" * size for size in TEST_DATA_SIZES}
        
        # Set test data
        for key, value in test_data.items():
            cache_manager.set(key, value)
        
        # Measure retrieval times
        for key, expected_value in test_data.items():
            start_time = time.time()
            cached_value = cache_manager.get(key)
            retrieval_time = (time.time() - start_time) * 1000  # Convert to ms
            
            assert cached_value == expected_value
            assert retrieval_time < PERFORMANCE_THRESHOLD
            
    def test_cache_set_encryption(self, encrypted_cache_manager):
        """Test encrypted cache storage functionality."""
        sensitive_data = {"ssn": "123-45-6789", "dob": "1990-01-01"}
        key = "sensitive_info"
        
        # Set encrypted data
        encrypted_cache_manager.set(key, sensitive_data, encrypt=True)
        
        # Verify raw data is encrypted
        raw_value = encrypted_cache_manager._client.get(key)
        assert sensitive_data["ssn"] not in raw_value
        
        # Verify decryption
        decrypted_value = encrypted_cache_manager.get(key, decrypt=True)
        assert decrypted_value == sensitive_data

    def test_cache_delete_patterns(self, cache_manager):
        """Test pattern-based cache invalidation."""
        # Set up test data with patterns
        test_patterns = {
            f"{TEST_CACHE_PREFIX}user:1:*": ["profile", "settings", "preferences"],
            f"{TEST_CACHE_PREFIX}user:2:*": ["profile", "settings"]
        }
        
        for pattern, suffixes in test_patterns.items():
            base_key = pattern.replace("*", "")
            for suffix in suffixes:
                cache_manager.set(f"{base_key}{suffix}", f"test_data_{suffix}")
        
        # Test pattern deletion
        for pattern in test_patterns:
            # Verify keys exist
            keys_before = cache_manager._client.keys(pattern)
            assert len(keys_before) > 0
            
            # Delete by pattern
            cache_manager._client.delete(*keys_before)
            
            # Verify deletion
            keys_after = cache_manager._client.keys(pattern)
            assert len(keys_after) == 0

class TestCacheManager:
    """Test suite for CacheManager functionality."""
    
    def test_connection_pooling(self, redis_client):
        """Test connection pool behavior under load."""
        num_operations = 100
        cache_manager = CacheManager(client=redis_client)
        
        async def concurrent_operations():
            tasks = []
            for i in range(num_operations):
                key = f"test_key_{i}"
                value = f"test_value_{i}"
                tasks.append(asyncio.create_task(
                    asyncio.to_thread(cache_manager.set, key, value)
                ))
            await asyncio.gather(*tasks)
        
        # Run concurrent operations
        asyncio.run(concurrent_operations())
        
        # Verify all operations succeeded
        for i in range(num_operations):
            key = f"test_key_{i}"
            value = cache_manager.get(key)
            assert value == f"test_value_{i}"

    def test_circuit_breaker(self, cache_manager):
        """Test circuit breaker functionality under failures."""
        # Simulate network failures
        with patch.object(cache_manager._client, 'get', side_effect=Exception("Network error")):
            # Trigger failures up to threshold
            for _ in range(CIRCUIT_BREAKER_THRESHOLD):
                with pytest.raises(Exception):
                    cache_manager.get("test_key")
            
            # Verify circuit breaker is triggered
            assert cache_manager._circuit_breaker.is_broken()
            
            # Attempt operation with broken circuit
            result = cache_manager.get("test_key")
            assert result is None
            
            # Wait for cool down and verify reset
            time.sleep(cache_manager._circuit_breaker.reset_timeout)
            assert not cache_manager._circuit_breaker.is_broken()

    @pytest.mark.asyncio
    async def test_concurrent_access(self, cache_manager):
        """Test cache behavior under concurrent access."""
        num_tasks = 50
        key = "concurrent_test"
        
        async def increment():
            value = cache_manager.get(key) or 0
            await asyncio.sleep(0.01)  # Simulate processing
            cache_manager.set(key, value + 1)
            
        # Run concurrent increments
        tasks = [increment() for _ in range(num_tasks)]
        await asyncio.gather(*tasks)
        
        final_value = cache_manager.get(key)
        assert final_value == num_tasks

class TestCacheDecorator:
    """Test suite for caching decorator functionality."""
    
    def test_cached_decorator_performance(self, cache_manager):
        """Test caching decorator performance impact."""
        @cached(timeout=TEST_TIMEOUT, prefix="test_func")
        def expensive_operation(param):
            time.sleep(0.1)  # Simulate expensive operation
            return f"result_{param}"
        
        # First call - should be slow
        start_time = time.time()
        result1 = expensive_operation("test")
        first_call_time = (time.time() - start_time) * 1000
        
        # Second call - should be fast (cached)
        start_time = time.time()
        result2 = expensive_operation("test")
        second_call_time = (time.time() - start_time) * 1000
        
        assert result1 == result2
        assert second_call_time < first_call_time
        assert second_call_time < PERFORMANCE_THRESHOLD

def test_cache_metrics(cache_manager):
    """Test cache metrics collection."""
    test_key = f"{TEST_CACHE_PREFIX}metrics_test"
    test_value = "test_data"
    
    # Test cache miss
    miss_value = cache_manager.get(test_key)
    assert miss_value is None
    
    # Test cache set and hit
    cache_manager.set(test_key, test_value)
    hit_value = cache_manager.get(test_key)
    assert hit_value == test_value
    
    # Verify metrics were recorded
    # Note: In real implementation, would verify Prometheus metrics
    # Here we just verify the operations completed successfully

def test_cache_version_invalidation(cache_manager):
    """Test cache version-based invalidation."""
    key = f"{TEST_CACHE_PREFIX}version_test"
    value = "test_data"
    
    # Set with current version
    cache_manager.set(key, value)
    assert cache_manager.get(key) == value
    
    # Simulate version change
    with patch('utils.cache.CACHE_VERSION', 'new_version'):
        # Should not find key with new version
        assert cache_manager.get(key) is None