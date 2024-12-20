"""
Django settings initialization module for Transfer Requirements Management System.
Dynamically loads environment-specific settings based on DJANGO_ENV environment variable.
"""

# v3.11+
import os
# v3.11+
import logging

# Initialize logging
logger = logging.getLogger(__name__)

# Define environment settings
DJANGO_ENV = os.getenv('DJANGO_ENV', 'development')
ALLOWED_ENVIRONMENTS = ['development', 'staging', 'production']

def validate_environment() -> bool:
    """
    Validates that DJANGO_ENV is set to an allowed environment value.
    
    Returns:
        bool: True if environment is valid
        
    Raises:
        ValueError: If DJANGO_ENV is not in ALLOWED_ENVIRONMENTS
    """
    if DJANGO_ENV not in ALLOWED_ENVIRONMENTS:
        error_msg = f"Invalid DJANGO_ENV: {DJANGO_ENV}. Must be one of: {', '.join(ALLOWED_ENVIRONMENTS)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Environment validated: {DJANGO_ENV}")
    return True

def get_settings_module() -> str:
    """
    Determines which settings module to load based on DJANGO_ENV.
    
    Returns:
        str: Full module path for environment-specific settings
        
    Raises:
        ValueError: If environment validation fails
    """
    # Validate environment before proceeding
    validate_environment()
    
    # Map environments to settings modules
    settings_map = {
        'development': 'config.settings.development',
        'staging': 'config.settings.production',  # Staging uses production settings with overrides
        'production': 'config.settings.production'
    }
    
    module_path = settings_map[DJANGO_ENV]
    logger.info(f"Loading settings module: {module_path}")
    return module_path

def validate_settings() -> bool:
    """
    Validates that all required Django settings are present and correctly configured.
    
    Returns:
        bool: True if all settings are valid
        
    Raises:
        ImproperlyConfigured: If any required settings are missing or invalid
    """
    from django.core.exceptions import ImproperlyConfigured
    
    # Required settings to validate
    required_settings = {
        'INSTALLED_APPS': list,
        'MIDDLEWARE': list,
        'DATABASES': dict,
        'SECRET_KEY': str,
        'ALLOWED_HOSTS': list
    }
    
    # Get current module's attributes
    current_settings = globals()
    
    # Validate required settings
    for setting, expected_type in required_settings.items():
        if setting not in current_settings:
            error_msg = f"Required setting {setting} is missing"
            logger.error(error_msg)
            raise ImproperlyConfigured(error_msg)
            
        if not isinstance(current_settings[setting], expected_type):
            error_msg = f"Setting {setting} must be of type {expected_type.__name__}"
            logger.error(error_msg)
            raise ImproperlyConfigured(error_msg)
    
    # Additional production-specific validations
    if DJANGO_ENV == 'production':
        if not current_settings.get('SECURE_SSL_REDIRECT'):
            error_msg = "SECURE_SSL_REDIRECT must be True in production"
            logger.error(error_msg)
            raise ImproperlyConfigured(error_msg)
            
        if not current_settings.get('SECURE_HSTS_SECONDS'):
            error_msg = "SECURE_HSTS_SECONDS must be set in production"
            logger.error(error_msg)
            raise ImproperlyConfigured(error_msg)
            
        if not current_settings.get('SECURE_PROXY_SSL_HEADER'):
            error_msg = "SECURE_PROXY_SSL_HEADER must be configured in production"
            logger.error(error_msg)
            raise ImproperlyConfigured(error_msg)
    
    logger.info("Settings validation completed successfully")
    return True

# Load environment-specific settings
settings_module = get_settings_module()
exec(f"from {settings_module} import *")

# Validate loaded settings
validate_settings()

# Export environment information
__all__ = ['DJANGO_ENV', 'get_settings_module', 'validate_settings']