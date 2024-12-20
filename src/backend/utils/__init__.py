"""
Core utilities package for the Transfer Requirements Management System.
Provides centralized access to AWS integrations, caching functionality,
validation utilities, and enhanced error handling.

Version: 1.0.0
"""

# AWS service clients
from .aws import (  # v1.26.0
    S3Client,
    SESClient, 
    KMSClient,
    upload_file_to_s3,
    send_email
)

# Caching utilities
from .cache import (  # v1.0.0
    CacheManager,
    cached,
    CACHE_VERSION,
    DEFAULT_TIMEOUT
)

# Validation utilities
from .validators import (  # v1.0.0
    validate_course_code,
    validate_credits,
    validate_institution_type,
    validate_requirement_rules,
    validation_decorator,
    VALID_DEPARTMENT_CODES,
    VALID_INSTITUTION_TYPES,
    COURSE_CODE_PATTERN
)

# Exception classes
from .exceptions import (  # v1.0.0
    BaseAPIException,
    ValidationError,
    AuthenticationError,
    PermissionDeniedError,
    NotFoundError,
    ServerError
)

# Version information
__version__ = '1.0.0'
__author__ = 'Transfer Requirements Management System Team'

# Package metadata
__all__ = [
    # AWS clients
    'S3Client',
    'SESClient',
    'KMSClient',
    'upload_file_to_s3',
    'send_email',
    
    # Caching
    'CacheManager',
    'cached',
    'CACHE_VERSION',
    'DEFAULT_TIMEOUT',
    
    # Validation
    'validate_course_code',
    'validate_credits', 
    'validate_institution_type',
    'validate_requirement_rules',
    'validation_decorator',
    'VALID_DEPARTMENT_CODES',
    'VALID_INSTITUTION_TYPES',
    'COURSE_CODE_PATTERN',
    
    # Exceptions
    'BaseAPIException',
    'ValidationError',
    'AuthenticationError',
    'PermissionDeniedError',
    'NotFoundError',
    'ServerError'
]

# Configure default logging
import logging
logger = logging.getLogger(__name__)

def get_version():
    """Return the current version of the utils package."""
    return __version__

def configure_logging(level=logging.INFO):
    """
    Configure default logging settings for the utils package.
    
    Args:
        level: Logging level to use (default: INFO)
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )