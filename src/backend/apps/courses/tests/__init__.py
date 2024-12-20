"""
Test package initialization for the courses app providing comprehensive test configuration
and fixtures for ensuring 99.99% accuracy in course validation testing.

Version: 1.0
"""

import pytest  # v7.0+
from unittest.mock import Mock, patch  # v3.11+
from freezegun import freeze_time  # v1.2+
from django.utils import timezone
from apps.courses.models import Course
from typing import Dict, Any, List
import uuid

# Define test plugins for comprehensive coverage
pytest_plugins = [
    'pytest-django',  # For Django test database handling
    'pytest-cov',    # For coverage reporting
    'pytest-xdist'   # For parallel test execution
]

def pytest_configure(config: pytest.Config) -> None:
    """
    Configure pytest environment with comprehensive test settings.
    
    Args:
        config: pytest configuration object
    """
    # Configure Django test database settings
    config.addinivalue_line(
        "markers",
        "django_db: Mark test to use Django test database"
    )
    
    # Configure test coverage settings for 99.99% accuracy
    config.option.cov_report = {
        'html': 'coverage/html',
        'xml': 'coverage/xml',
        'term-missing': True,
        'fail_under': 99.99
    }
    
    # Configure parallel test execution
    config.option.numprocesses = 'auto'
    
    # Set up test environment variables
    config.addinivalue_line(
        "env",
        "TESTING=true"
    )
    
    # Configure logging for test execution
    config.option.log_level = 'DEBUG'
    config.option.log_format = '%(asctime)s %(levelname)s %(message)s'
    config.option.log_date_format = '%Y-%m-%d %H:%M:%S'

@pytest.fixture(scope='function')
@freeze_time('2024-01-01')
class CourseTestFixture:
    """
    Comprehensive test fixture providing sample course data and validation scenarios.
    """
    def __init__(self):
        """Initialize test data with various validation scenarios."""
        self.sample_course = None
        self.sample_equivalency = None
        self.validation_scenarios = {}
        self.time_dependent_data = {}
        
        # Initialize test data
        self.setup()

    def setup(self) -> None:
        """
        Set up comprehensive test course data with proper isolation.
        """
        # Create sample course with complete valid data
        self.sample_course = {
            'id': uuid.uuid4(),
            'institution_id': uuid.uuid4(),
            'code': 'CS 101',
            'name': 'Introduction to Computer Science',
            'description': 'Foundational computer science concepts',
            'credits': '3.00',
            'metadata': {
                'delivery_mode': 'in_person',
                'learning_outcomes': ['outcome1', 'outcome2']
            },
            'status': 'active',
            'valid_from': timezone.now(),
            'valid_to': None,
            'validation_errors': []
        }

        # Set up validation test scenarios
        self.validation_scenarios = {
            'invalid_code': {
                'code': 'invalid',
                'expected_error': 'Invalid course code format'
            },
            'invalid_credits': {
                'credits': '15.00',
                'expected_error': 'Credits must be between 0.0 and 12.0'
            },
            'invalid_metadata': {
                'metadata': {},
                'expected_error': 'Missing required fields'
            },
            'invalid_dates': {
                'valid_from': timezone.now(),
                'valid_to': timezone.now() - timezone.timedelta(days=1),
                'expected_error': 'End date must be after start date'
            }
        }

        # Set up time-dependent test data
        self.time_dependent_data = {
            'future_course': {
                **self.sample_course,
                'valid_from': timezone.now() + timezone.timedelta(days=30)
            },
            'expired_course': {
                **self.sample_course,
                'valid_to': timezone.now() - timezone.timedelta(days=1)
            },
            'current_course': {
                **self.sample_course,
                'valid_from': timezone.now() - timezone.timedelta(days=30),
                'valid_to': timezone.now() + timezone.timedelta(days=30)
            }
        }

        # Set up course equivalency test data
        self.sample_equivalency = {
            'source_course_id': self.sample_course['id'],
            'target_course_id': uuid.uuid4(),
            'effective_date': timezone.now(),
            'expiration_date': None,
            'metadata': {
                'transfer_ratio': 1.0,
                'notes': 'Direct equivalency'
            },
            'validation_status': 'approved'
        }

        # Mock external dependencies
        self.mock_institution = Mock(
            id=self.sample_course['institution_id'],
            code='TESTINST',
            name='Test Institution',
            type='university'
        )

        # Set up prerequisite test data
        self.prerequisite_scenarios = {
            'valid_chain': ['CS 101', 'CS 102', 'CS 201'],
            'circular_dependency': ['CS 101', 'CS 102', 'CS 101'],
            'invalid_course': ['CS 101', 'INVALID']
        }

        # Clear any cached data
        Course.objects.all().delete()