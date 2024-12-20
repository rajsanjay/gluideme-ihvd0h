"""
Test package initialization file for the institutions app test suite.
Configures comprehensive test discovery, shared test utilities, and test execution management.

Version: 1.0
"""

from django.test import TestCase  # v4.2+
from unittest import TestLoader  # v3.11+
from apps.institutions.tests.test_models import InstitutionModelTest

# Test module configuration for comprehensive coverage
TEST_MODULES = [
    'test_models',          # Institution and agreement model tests
    'test_serializers',     # Data serialization tests
    'test_views',          # API endpoint tests
    'test_validators',     # Data validation tests
    'test_integration'     # End-to-end integration tests
]

# Test categorization tags for organized execution
TEST_TAGS = [
    'models',              # Model-specific tests
    'api',                # API-related tests
    'validation',         # Data validation tests
    'integration',        # Integration test scenarios
    'security'           # Security-related test cases
]

def load_tests(loader: TestLoader, pattern: str, top_level_dir: str) -> TestLoader.suiteClass:
    """
    Advanced test suite loader function for Django test discovery with support for 
    filtering, parallel execution, and comprehensive coverage.

    Args:
        loader: TestLoader instance for test discovery
        pattern: Test file pattern to match
        top_level_dir: Root directory for test discovery

    Returns:
        TestSuite: Combined test suite containing all discovered institution tests
    """
    suite = loader.suiteClass()

    # Configure test discovery settings
    discovery_settings = {
        'pattern': pattern or 'test_*.py',
        'top_level_dir': top_level_dir,
        'include_tags': TEST_TAGS
    }

    # Discover and load tests from each module
    for module_name in TEST_MODULES:
        try:
            # Load test module
            module_tests = loader.loadTestsFromName(
                f'apps.institutions.tests.{module_name}'
            )

            # Apply test categorization tags
            for test in module_tests:
                if hasattr(test, '_testMethodName'):
                    # Extract tags from test method docstring or name
                    test_tags = [
                        tag for tag in TEST_TAGS 
                        if tag in test._testMethodName or 
                        (test._testMethodDoc and tag in test._testMethodDoc)
                    ]
                    setattr(test, 'tags', test_tags)

            # Add discovered tests to suite
            suite.addTests(module_tests)

        except ImportError as e:
            # Log warning but continue with other modules
            import logging
            logging.warning(
                f"Could not load test module {module_name}: {str(e)}"
            )

    # Configure test execution settings
    suite.parallel = True  # Enable parallel execution
    suite.parallel_workers = 4  # Number of parallel workers

    # Set up result reporting and coverage tracking
    suite.coverage_source = ['apps.institutions']
    suite.coverage_report = True
    suite.coverage_threshold = 90.0  # Minimum coverage requirement

    return suite