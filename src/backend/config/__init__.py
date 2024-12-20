"""
Transfer Requirements Management System Configuration Package.

This module initializes Django configuration settings based on the environment
and provides version information for the system.

Version: 1.0.0
Environment Support: development, staging, production, test
"""

import os  # v3.11+
import logging
from importlib import import_module
from typing import Optional

# Version information
VERSION = '1.0.0'

# Environment configuration
ENVIRONMENT = os.getenv('DJANGO_ENV', 'development')
VALID_ENVIRONMENTS = ['development', 'staging', 'production', 'test']

# Configure logging
logger = logging.getLogger(__name__)

def validate_environment() -> bool:
    """
    Validates the current environment configuration and required variables.
    
    Returns:
        bool: True if environment is valid
    
    Raises:
        ValueError: If environment validation fails
    """
    if ENVIRONMENT not in VALID_ENVIRONMENTS:
        raise ValueError(
            f"Invalid environment '{ENVIRONMENT}'. "
            f"Must be one of: {', '.join(VALID_ENVIRONMENTS)}"
        )
    
    # Required environment variables for all environments
    required_vars = [
        'DJANGO_SECRET_KEY',
        'DB_NAME',
        'DB_USER',
        'DB_PASSWORD',
        'DB_HOST',
        'DB_PORT',
        'REDIS_URL',
        'JWT_SIGNING_KEY'
    ]
    
    # Additional required variables for production/staging
    if ENVIRONMENT in ['production', 'staging']:
        required_vars.extend([
            'SENTRY_DSN',
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'AWS_STORAGE_BUCKET_NAME',
            'MEILISEARCH_HOST',
            'MEILISEARCH_API_KEY',
            'PINECONE_API_KEY',
            'PINECONE_ENVIRONMENT',
            'APM_SERVER_URL'
        ])
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables for {ENVIRONMENT} environment: "
            f"{', '.join(missing_vars)}"
        )
    
    logger.info(f"Environment '{ENVIRONMENT}' validated successfully")
    return True

def get_settings_module() -> str:
    """
    Determines and validates the appropriate settings module based on environment.
    
    Returns:
        str: Full Python path to the validated settings module
    
    Raises:
        ValueError: If settings module cannot be determined or loaded
    """
    try:
        validate_environment()
        
        # Map environments to settings modules
        settings_map = {
            'development': 'config.settings.development',
            'staging': 'config.settings.staging',
            'production': 'config.settings.production',
            'test': 'config.settings.test'
        }
        
        settings_module = settings_map.get(ENVIRONMENT)
        if not settings_module:
            raise ValueError(f"No settings module mapped for environment: {ENVIRONMENT}")
        
        # Verify module exists
        try:
            import_module(settings_module)
        except ImportError as e:
            raise ValueError(f"Could not import settings module '{settings_module}': {str(e)}")
        
        logger.info(f"Using settings module: {settings_module}")
        return settings_module
        
    except Exception as e:
        logger.error(f"Failed to determine settings module: {str(e)}")
        raise

# Validate environment on module import
validate_environment()

# Export version and environment information
__version__ = VERSION
__all__ = ['VERSION', 'ENVIRONMENT', 'get_settings_module', 'validate_environment']