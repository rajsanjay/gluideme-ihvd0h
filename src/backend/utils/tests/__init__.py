"""
Test module initialization file for the utils package test suite.
Configures test environment and imports test modules for AWS utilities, caching, and validation functions.

Version: 1.0
Author: Transfer Requirements Management System Team
"""

# Import test modules to make them available to test runner
from utils.tests.test_aws import TestAWSClient, TestS3Operations, TestEmailOperations
from utils.tests.test_cache import (
    TestCacheUtils,
    TestCacheManager,
    TestCacheDecorator,
    test_cache_metrics,
    test_cache_version_invalidation
)
from utils.tests.test_validators import (
    TestCourseCodeValidator,
    TestCreditsValidator,
    TestInstitutionTypeValidator,
    TestRequirementRulesValidator
)

# Configure pytest plugins for Django test environment
pytest_plugins = [
    'pytest_django.fixtures',  # Django test fixtures
]

# Export test classes for discovery
__all__ = [
    # AWS test classes
    'TestAWSClient',
    'TestS3Operations', 
    'TestEmailOperations',
    
    # Cache test classes
    'TestCacheUtils',
    'TestCacheManager',
    'TestCacheDecorator',
    'test_cache_metrics',
    'test_cache_version_invalidation',
    
    # Validator test classes
    'TestCourseCodeValidator',
    'TestCreditsValidator',
    'TestInstitutionTypeValidator',
    'TestRequirementRulesValidator'
]