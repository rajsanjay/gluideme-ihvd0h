"""
Test package initialization for the validation app test suite.
Configures pytest settings, fixtures, and comprehensive testing infrastructure 
for validation rules, sessions, and history tracking.

Version: 1.0
"""

import pytest  # v7.0+
from django.test import TestCase  # v4.2+
from apps.validation.models import ValidationRule, ValidationSession
from typing import Dict, List

# Comprehensive test fixtures for validation testing
TEST_FIXTURES = {
    'rule_types': [
        'course_match',
        'credit_requirement', 
        'prerequisite_check',
        'grade_requirement',
        'unit_conversion',
        'course_sequence',
        'major_requirement',
        'transfer_agreement'
    ],
    'validation_statuses': [
        'pending',
        'in_progress',
        'completed',
        'failed',
        'partial_match',
        'needs_review',
        'expired',
        'superseded'
    ],
    'accuracy_thresholds': {
        'exact_match': 0.9999,  # 99.99% accuracy requirement
        'partial_match': 0.95,
        'manual_review': 0.90
    },
    'test_metadata': {
        'validation_tracking': True,
        'history_enabled': True,
        'performance_metrics': True
    }
}

def pytest_configure(config: pytest.Config) -> None:
    """
    Configure pytest settings for comprehensive validation testing.
    
    Args:
        config: Pytest configuration object
        
    Configures:
        - Database settings
        - Custom markers
        - Test fixtures
        - Parallel execution
        - Metrics collection
    """
    # Register custom markers for validation testing
    config.addinivalue_line(
        "markers",
        "validation: mark test as validation test with accuracy tracking"
    )
    config.addinivalue_line(
        "markers", 
        "accuracy: mark test for accuracy threshold validation"
    )
    config.addinivalue_line(
        "markers",
        "integration: mark test as validation integration test"
    )

    # Configure test database settings
    config.option.reuse_db = True  # Reuse test database for performance
    config.option.nomigrations = True  # Skip migrations in tests
    
    # Setup database isolation levels for validation testing
    config.option.ds_isolation = "READ COMMITTED"
    
    # Configure parallel test execution
    config.option.numprocesses = 'auto'
    
    # Setup test metrics collection
    config.option.verbose = 2  # Detailed test output
    config.option.durations = 10  # Show slowest 10 tests
    config.option.durations_min = 1.0  # Min duration to show
    
    # Configure validation history tracking
    config.option.capture = "no"  # Show validation progress
    
    # Setup test data generators
    config.option.randomly_seed = None  # Random but reproducible
    
    # Configure validation accuracy thresholds
    config.option.strict = True  # Enforce accuracy requirements
    
    # Register custom test fixtures
    pytest.fixture(autouse=True)(setup_validation_fixtures)
    pytest.fixture(scope='session')(setup_accuracy_tracking)

def setup_validation_fixtures(request: pytest.FixtureRequest) -> Dict:
    """
    Setup test fixtures for validation testing.
    
    Args:
        request: Pytest fixture request
        
    Returns:
        Dict: Test fixture configuration
    """
    return TEST_FIXTURES

def setup_accuracy_tracking(request: pytest.FixtureRequest) -> None:
    """
    Configure accuracy tracking for validation tests.
    
    Args:
        request: Pytest fixture request
    """
    def track_validation_accuracy(item: pytest.Item, nextitem: pytest.Item) -> None:
        if item.get_closest_marker('validation'):
            accuracy = getattr(item, 'validation_accuracy', None)
            if accuracy and accuracy < TEST_FIXTURES['accuracy_thresholds']['exact_match']:
                pytest.fail(f"Validation accuracy {accuracy} below required threshold")
    
    request.addfinalizer(track_validation_accuracy)

# Export test configuration
__all__ = ['pytest_configure', 'TEST_FIXTURES']