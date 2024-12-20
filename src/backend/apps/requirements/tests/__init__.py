"""
Test package initialization for the requirements app test suite.
Configures pytest settings, coverage thresholds, and provides standardized test fixtures.

Version: 1.0
"""

# pytest v7.4+
import pytest
# freezegun v1.2+
from freezegun import freeze_time
from apps.requirements.models import (
    TransferRequirement,
    REQUIREMENT_TYPES,
    REQUIREMENT_STATUS
)
from uuid import uuid4
from datetime import datetime, timedelta

# Standardized test data fixture for transfer requirements
TEST_REQUIREMENT_DATA = {
    'source_institution_id': uuid4(),
    'target_institution_id': uuid4(),
    'major_code': 'CS',
    'title': 'Computer Science Transfer Requirements',
    'description': 'Comprehensive transfer requirements for Computer Science major',
    'type': 'major',
    'rules': {
        'courses': [
            {
                'code': 'CS101',
                'credits': 4.0
            },
            {
                'code': 'MATH101',
                'credits': 4.0
            }
        ],
        'min_credits': 60.0,
        'prerequisites': {
            'CS101': [],
            'MATH101': []
        }
    },
    'metadata': {
        'version_notes': 'Initial version',
        'reviewer_id': str(uuid4()),
        'approval_date': datetime.now().isoformat()
    },
    'status': 'published',
    'effective_date': datetime.now(),
    'expiration_date': datetime.now() + timedelta(days=365),
    'validation_accuracy': 100.0
}

# Standardized test data fixture for course validation
TEST_COURSE_DATA = {
    'code': 'CS101',
    'name': 'Introduction to Programming',
    'description': 'Fundamental programming concepts and problem solving',
    'credits': 4.0,
    'metadata': {
        'delivery_mode': 'in_person',
        'learning_outcomes': [
            'Understand basic programming concepts',
            'Implement simple algorithms',
            'Debug and test code'
        ],
        'prerequisites_description': 'None',
        'additional_requirements': {
            'lab_required': True,
            'computer_required': True
        },
        'transfer_agreements': []
    },
    'status': 'active',
    'valid_from': datetime.now(),
    'valid_to': datetime.now() + timedelta(days=365),
    'validation_errors': []
}

def pytest_configure(config):
    """
    Configure pytest settings including coverage thresholds, custom markers,
    and test collection rules.
    """
    # Register custom markers
    config.addinivalue_line(
        "markers",
        "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers",
        "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers",
        "requirement: mark test as a requirement validation test"
    )
    config.addinivalue_line(
        "markers",
        "course: mark test as a course validation test"
    )

    # Configure coverage settings
    config.option.cov_fail_under = 90.0  # Enforce 90% minimum coverage
    config.option.cov_report = {
        'term-missing': True,
        'html': True,
        'xml': True
    }

    # Configure coverage exclusions
    config.option.cov_config = '.coveragerc'
    config.option.cov_branch = True

    # Set test collection rules
    config.option.testpaths = ['tests']
    config.option.python_files = ['test_*.py']
    config.option.python_classes = ['Test*']
    config.option.python_functions = ['test_*']

    # Configure test execution order
    config.option.order = 'definition'