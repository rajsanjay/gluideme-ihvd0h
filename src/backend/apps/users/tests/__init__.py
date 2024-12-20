"""
Test package initialization for the users app test suite.
Configures test environment, imports test modules, and defines shared test utilities.

Version: 1.0
"""

# Test framework imports - v7+
import pytest

# Internal test module imports
from apps.users.tests.test_models import *
from apps.users.tests.test_serializers import *
from apps.users.tests.test_views import *

# Test user roles based on system requirements
TEST_USER_ROLES = [
    'admin',
    'institution_admin', 
    'counselor',
    'student',
    'guest'
]

# Default test user data with secure password
TEST_USER_DATA = {
    'email': 'test@example.com',
    'password': 'SecurePass123!@#',
    'first_name': 'Test',
    'last_name': 'User',
    'role': 'student',
    'preferences': {
        'notification_settings': {
            'email_notifications': True,
            'web_notifications': True
        },
        'display_preferences': {
            'theme': 'light',
            'language': 'en'
        }
    },
    'security_settings': {
        'failed_login_attempts': 0,
        'require_password_change': False,
        'last_password_change': None
    }
}

# Default admin user data
TEST_ADMIN_DATA = {
    'email': 'admin@example.com',
    'password': 'AdminPass123!@#',
    'first_name': 'Admin',
    'last_name': 'User',
    'role': 'admin',
    'preferences': {
        'notification_settings': {
            'email_notifications': True,
            'web_notifications': True
        },
        'display_preferences': {
            'theme': 'dark',
            'language': 'en'
        }
    },
    'security_settings': {
        'failed_login_attempts': 0,
        'require_password_change': False,
        'last_password_change': None
    }
}

def pytest_configure(config):
    """
    Configure pytest for the users app test suite.
    Sets up test environment, registers markers, and configures test database.

    Args:
        config: Pytest config object
    """
    # Register custom markers for user tests
    config.addinivalue_line(
        "markers",
        "auth: Authentication and authorization tests"
    )
    config.addinivalue_line(
        "markers", 
        "security: Security and validation tests"
    )
    config.addinivalue_line(
        "markers",
        "performance: Performance and optimization tests"
    )

    # Configure test database settings
    config.option.reuse_db = True
    config.option.nomigrations = True

    # Configure authentication test settings
    config.option.auth_backends = [
        'django.contrib.auth.backends.ModelBackend',
    ]

    # Configure test email backend
    config.option.email_backend = 'django.core.mail.backends.locmem.EmailBackend'

    # Configure test cache backend
    config.option.cache_backend = 'django.core.cache.backends.locmem.LocMemCache'

    # Configure test security settings
    config.option.password_hashers = [
        'django.contrib.auth.hashers.MD5PasswordHasher',
    ]

    # Configure test rate limiting
    config.option.rate_limit = {
        'user_registration': '5/hour',
        'password_reset': '3/hour',
        'login_attempts': '5/hour'
    }

    # Configure test monitoring
    config.option.enable_metrics = False