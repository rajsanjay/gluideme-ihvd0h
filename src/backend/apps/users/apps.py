"""
Django application configuration for the users app implementing secure user management,
authentication, authorization, and role-based access control.

Version: Django 4.2+
"""

from django.apps import AppConfig  # Django 4.2+


class UsersConfig(AppConfig):
    """
    Configuration class for the users Django application implementing secure user
    management and role-based access control.
    
    This configuration sets up:
    - Secure ID generation using BigAutoField
    - JWT authentication settings
    - Field-level encryption for sensitive data
    - Role-based access control
    - Audit logging
    - Session security
    - Password validation
    - Rate limiting
    """

    # Use BigAutoField for secure ID generation with reduced collision risk
    default_auto_field = 'django.db.models.BigAutoField'
    
    # Application namespace for Django discovery
    name = 'apps.users'
    
    # Human-readable name for admin interface
    verbose_name = 'Users'

    def ready(self):
        """
        Perform secure application initialization and setup security configurations.
        This method is called by Django when the application is ready to be used.
        
        Initializes:
        - Role-based access control settings
        - JWT token configuration
        - Field-level encryption
        - Audit logging
        - Session security
        - Password validation
        - Rate limiting
        """
        # Import signal handlers and receivers
        from . import signals  # noqa

        # Initialize role-based access control
        self.setup_rbac()
        
        # Configure JWT authentication
        self.setup_jwt_auth()
        
        # Set up field-level encryption
        self.setup_encryption()
        
        # Initialize audit logging
        self.setup_audit_logging()
        
        # Configure session security
        self.setup_session_security()
        
        # Set up password validation
        self.setup_password_validation()
        
        # Initialize rate limiting
        self.setup_rate_limiting()

    def setup_rbac(self):
        """
        Configure role-based access control settings for different user types:
        - Admin
        - Institution Admin
        - Counselor
        - Student
        - Guest
        """
        from django.conf import settings
        
        # Define default roles if not already configured
        if not hasattr(settings, 'USER_ROLES'):
            settings.USER_ROLES = {
                'ADMIN': 'admin',
                'INSTITUTION_ADMIN': 'institution_admin',
                'COUNSELOR': 'counselor',
                'STUDENT': 'student',
                'GUEST': 'guest'
            }

    def setup_jwt_auth(self):
        """
        Configure secure JWT authentication settings:
        - 15-minute access token lifetime
        - 7-day refresh token lifetime
        - Required security algorithms
        """
        from django.conf import settings
        from datetime import timedelta
        
        # Set JWT authentication settings if not configured
        if not hasattr(settings, 'SIMPLE_JWT'):
            settings.SIMPLE_JWT = {
                'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
                'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
                'ALGORITHM': 'HS256',
                'SIGNING_KEY': settings.SECRET_KEY,
                'AUTH_HEADER_TYPES': ('Bearer',),
                'ROTATE_REFRESH_TOKENS': True,
            }

    def setup_encryption(self):
        """
        Configure field-level encryption for sensitive user data using AWS KMS
        """
        from django.conf import settings
        
        # Set encryption settings if not configured
        if not hasattr(settings, 'FIELD_ENCRYPTION_KEYS'):
            settings.FIELD_ENCRYPTION_KEYS = {
                'PROVIDER': 'aws-kms',
                'KEY_ID': settings.AWS_KMS_KEY_ID,
                'REGION': settings.AWS_REGION
            }

    def setup_audit_logging(self):
        """
        Initialize audit logging for user actions and security events
        """
        from django.conf import settings
        import logging
        
        # Configure audit logger if not already set
        if 'audit' not in settings.LOGGING['loggers']:
            settings.LOGGING['loggers']['audit'] = {
                'handlers': ['cloudwatch'],
                'level': 'INFO',
                'propagate': True,
            }

    def setup_session_security(self):
        """
        Configure secure session settings:
        - 30-minute session timeout
        - Secure cookie settings
        - CSRF protection
        """
        from django.conf import settings
        
        # Set session security settings
        settings.SESSION_COOKIE_SECURE = True
        settings.SESSION_COOKIE_HTTPONLY = True
        settings.SESSION_COOKIE_SAMESITE = 'Strict'
        settings.SESSION_EXPIRE_AT_BROWSER_CLOSE = True
        settings.SESSION_COOKIE_AGE = 1800  # 30 minutes

    def setup_password_validation(self):
        """
        Configure secure password validation rules
        """
        from django.conf import settings
        
        # Set password validators if not configured
        if not hasattr(settings, 'AUTH_PASSWORD_VALIDATORS'):
            settings.AUTH_PASSWORD_VALIDATORS = [
                {
                    'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
                },
                {
                    'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
                    'OPTIONS': {
                        'min_length': 12,
                    }
                },
                {
                    'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
                },
                {
                    'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
                },
            ]

    def setup_rate_limiting(self):
        """
        Initialize rate limiting for authentication endpoints
        """
        from django.conf import settings
        
        # Configure rate limiting settings if not set
        if not hasattr(settings, 'REST_FRAMEWORK'):
            settings.REST_FRAMEWORK = {
                'DEFAULT_THROTTLE_CLASSES': [
                    'rest_framework.throttling.AnonRateThrottle',
                    'rest_framework.throttling.UserRateThrottle'
                ],
                'DEFAULT_THROTTLE_RATES': {
                    'anon': '100/hour',
                    'user': '1000/hour',
                    'auth': '5/minute',
                }
            }


# Default app configuration for Django discovery
default_app_config = 'apps.users.apps.UsersConfig'