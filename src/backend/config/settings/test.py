"""
Test settings configuration for Transfer Requirements Management System.

This module extends the base settings and configures the environment specifically
for running automated tests with optimized performance and in-memory databases.
"""

# Import all settings from base configuration
from .base import *  # v4.2+

# Import required for temporary directory creation
import tempfile  # v3.11+

# Debug should be disabled in tests unless explicitly needed
DEBUG = True

# Use in-memory SQLite database for faster test execution
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'TEST': {
            # Disable serialization for faster tests
            'SERIALIZE': False,
            'NAME': None,
        },
    }
}

# Use in-memory cache for testing
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'test-cache',
        'TIMEOUT': 300,  # 5 minutes
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    }
}

# Use in-memory email backend for testing
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Configure Celery for synchronous execution during tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Use temporary directory for media files during tests
MEDIA_ROOT = tempfile.mkdtemp()

# Use fast password hasher for testing
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Configure search services for testing
MEILISEARCH_HOST = 'http://localhost:7700'
MEILISEARCH_API_KEY = 'test_key'
PINECONE_API_KEY = 'test_key'
PINECONE_ENVIRONMENT = 'test'

# Use the default test runner
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# Limit file upload size for tests
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB

# Use simple storage backend for static files in tests
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'