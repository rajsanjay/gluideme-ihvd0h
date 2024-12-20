"""
Enhanced Redis-based caching utility module for Transfer Requirements Management System.
Provides high availability, monitoring, and security features for optimized caching operations.

Version: 1.0
Author: Transfer Requirements Management System Team
"""

# External imports with versions
import redis  # v4.5+
import json  # Python stdlib
from typing import Any, Optional, Dict, Union, Callable  # Python stdlib
from functools import wraps  # Python stdlib
from contextlib import contextmanager  # Python stdlib
import hashlib  # Python stdlib
import os  # Python stdlib
from cryptography.fernet import Fernet  # v3.4+
from prometheus_client import Counter, Histogram  # v0.16+
import time
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Global constants
REDIS_CLIENT = redis.Redis(
    connection_pool=redis.ConnectionPool(
        host=os.getenv('REDIS_HOST', 'redis'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        db=0,
        max_connections=20,
        decode_responses=True
    )
)
DEFAULT_TIMEOUT = 3600  # 1 hour default cache timeout
KEY_PREFIX = 'trms'  # Transfer Requirements Management System prefix
CACHE_VERSION = '1.0'  # Cache version for invalidation control
MAX_RETRIES = 3  # Maximum retry attempts for cache operations
CIRCUIT_BREAKER_THRESHOLD = 5  # Number of failures before circuit breaks

# Prometheus metrics
CACHE_HITS = Counter('cache_hits_total', 'Total cache hits')
CACHE_MISSES = Counter('cache_misses_total', 'Total cache misses')
CACHE_ERRORS = Counter('cache_errors_total', 'Total cache errors')
CACHE_LATENCY = Histogram('cache_operation_latency_seconds', 'Cache operation latency')

class CircuitBreaker:
    """Circuit breaker implementation for cache failure protection."""
    
    def __init__(self, threshold: int = CIRCUIT_BREAKER_THRESHOLD):
        self.threshold = threshold
        self.failures = 0
        self.broken = False
        self.last_failure_time = 0
        self.reset_timeout = 60  # 60 seconds cool down

    def record_failure(self) -> None:
        """Record a failure and potentially break the circuit."""
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.threshold:
            self.broken = True
            logger.warning("Circuit breaker activated due to multiple failures")

    def record_success(self) -> None:
        """Record a success and reset failure count."""
        self.failures = 0
        self.broken = False

    def is_broken(self) -> bool:
        """Check if circuit is broken with cool down period."""
        if not self.broken:
            return False
        if time.time() - self.last_failure_time > self.reset_timeout:
            self.broken = False
            self.failures = 0
            return False
        return True

class CacheMetrics:
    """Cache metrics collector for monitoring and alerting."""
    
    @staticmethod
    def record_hit():
        CACHE_HITS.inc()

    @staticmethod
    def record_miss():
        CACHE_MISSES.inc()

    @staticmethod
    def record_error():
        CACHE_ERRORS.inc()

    @staticmethod
    @contextmanager
    def measure_latency():
        """Context manager for measuring cache operation latency."""
        start_time = time.time()
        try:
            yield
        finally:
            CACHE_LATENCY.observe(time.time() - start_time)

class CacheManager:
    """Enhanced cache manager with high availability and monitoring capabilities."""

    def __init__(
        self,
        client: Optional[redis.Redis] = None,
        default_timeout: Optional[int] = None,
        enable_encryption: bool = False
    ):
        """
        Initialize cache manager with connection pooling and monitoring.

        Args:
            client: Optional Redis client instance
            default_timeout: Optional default cache timeout in seconds
            enable_encryption: Whether to enable encryption for cached values
        """
        self._client = client or REDIS_CLIENT
        self._default_timeout = default_timeout or DEFAULT_TIMEOUT
        self._circuit_breaker = CircuitBreaker()
        self._metrics = CacheMetrics()
        self._encryption_enabled = enable_encryption
        
        if enable_encryption:
            encryption_key = os.getenv('CACHE_ENCRYPTION_KEY')
            if not encryption_key:
                raise ValueError("Encryption key required when encryption is enabled")
            self._cipher_suite = Fernet(encryption_key.encode())

        # Validate cluster health on initialization
        self._validate_connection()

    def _validate_connection(self) -> None:
        """Validate Redis connection and cluster health."""
        try:
            self._client.ping()
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise

    def generate_cache_key(
        self,
        prefix: str,
        *args: Any,
        namespace: Optional[str] = None,
        **kwargs: Dict[str, Any]
    ) -> str:
        """
        Generate a versioned and namespaced cache key with collision prevention.

        Args:
            prefix: Key prefix
            *args: Variable arguments for key generation
            namespace: Optional namespace
            **kwargs: Keyword arguments for key generation

        Returns:
            Versioned cache key string
        """
        # Combine components
        key_components = [KEY_PREFIX, namespace, prefix] if namespace else [KEY_PREFIX, prefix]
        
        # Add args and kwargs
        if args:
            key_components.extend([str(arg) for arg in args])
        if kwargs:
            # Sort kwargs for consistency
            sorted_kwargs = sorted(kwargs.items())
            key_components.extend([f"{k}:{v}" for k, v in sorted_kwargs])

        # Add version
        key_components.append(CACHE_VERSION)
        
        # Create deterministic string and hash
        key_string = ':'.join(str(c) for c in key_components if c is not None)
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:8]
        
        return f"{key_string}:{key_hash}"

    def get(
        self,
        key: str,
        decrypt: bool = False
    ) -> Optional[Any]:
        """
        Get value from cache with retries and monitoring.

        Args:
            key: Cache key
            decrypt: Whether to decrypt the value

        Returns:
            Cached value if exists, None otherwise
        """
        if self._circuit_breaker.is_broken():
            logger.warning("Circuit breaker active, skipping cache get")
            return None

        with self._metrics.measure_latency():
            for attempt in range(MAX_RETRIES):
                try:
                    value = self._client.get(key)
                    
                    if value is None:
                        self._metrics.record_miss()
                        return None

                    # Deserialize and optionally decrypt
                    deserialized = json.loads(value)
                    if decrypt and self._encryption_enabled:
                        deserialized = self._cipher_suite.decrypt(
                            deserialized.encode()
                        ).decode()

                    self._metrics.record_hit()
                    self._circuit_breaker.record_success()
                    return deserialized

                except (redis.RedisError, json.JSONDecodeError) as e:
                    logger.error(f"Cache get error (attempt {attempt + 1}): {str(e)}")
                    self._circuit_breaker.record_failure()
                    self._metrics.record_error()
                    
                    if attempt == MAX_RETRIES - 1:
                        raise

    def set(
        self,
        key: str,
        value: Any,
        timeout: Optional[int] = None,
        encrypt: bool = False
    ) -> bool:
        """
        Set value in cache with encryption support.

        Args:
            key: Cache key
            value: Value to cache
            timeout: Optional timeout in seconds
            encrypt: Whether to encrypt the value

        Returns:
            bool indicating success
        """
        if self._circuit_breaker.is_broken():
            logger.warning("Circuit breaker active, skipping cache set")
            return False

        with self._metrics.measure_latency():
            try:
                # Serialize and optionally encrypt
                serialized = json.dumps(value)
                if encrypt and self._encryption_enabled:
                    serialized = self._cipher_suite.encrypt(
                        serialized.encode()
                    ).decode()

                success = self._client.set(
                    key,
                    serialized,
                    ex=timeout or self._default_timeout
                )
                
                if success:
                    self._circuit_breaker.record_success()
                return bool(success)

            except (redis.RedisError, json.JSONDecodeError) as e:
                logger.error(f"Cache set error: {str(e)}")
                self._circuit_breaker.record_failure()
                self._metrics.record_error()
                raise

def cached(
    timeout: Optional[int] = None,
    prefix: Optional[str] = None,
    encrypt: bool = False
) -> Callable:
    """
    Enhanced caching decorator with versioning and encryption support.

    Args:
        timeout: Optional cache timeout in seconds
        prefix: Optional key prefix
        encrypt: Whether to encrypt cached values

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            cache_manager = CacheManager()
            
            # Generate cache key
            key = cache_manager.generate_cache_key(
                prefix or func.__name__,
                *args,
                **kwargs
            )
            
            # Try to get from cache
            cached_value = cache_manager.get(key, decrypt=encrypt)
            if cached_value is not None:
                return cached_value
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(key, result, timeout=timeout, encrypt=encrypt)
            return result
            
        return wrapper
    return decorator

# Export public interfaces
__all__ = ['CacheManager', 'cached']