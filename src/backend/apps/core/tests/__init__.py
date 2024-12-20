"""
Test package initializer for the core app's test suite.
Provides comprehensive test utilities, fixtures, and base test classes for testing core models,
data management, and security functionality.

Version: 1.0
"""

from django.test import TestCase  # v4.2+
from django.utils import timezone  # v4.2+
from apps.core.models import BaseModel
from typing import Dict, Any
import uuid

# Global test constants
TEST_TIMESTAMP = timezone.now()
TEST_DATA: Dict[str, Any] = {}

class CoreTestCase(TestCase):
    """
    Base test case class providing comprehensive utilities and fixtures for testing core app functionality,
    including data management and security features.
    """

    def __init__(self, *args, **kwargs):
        """Initialize core test case with common test data and timestamp management."""
        super().__init__(*args, **kwargs)
        self.test_data: Dict[str, Any] = {}
        self.test_timestamp = timezone.now()

    def setUp(self) -> None:
        """
        Set up test environment with proper isolation and data management.
        Configures test database, security context, and version tracking.
        """
        super().setUp()

        # Initialize test timestamp for temporal data testing
        self.test_timestamp = timezone.now()

        # Initialize clean test data dictionary
        self.test_data = {
            'test_id': uuid.uuid4(),
            'timestamp': self.test_timestamp,
            'metadata': {
                'test_run': True,
                'environment': 'test'
            }
        }

        # Configure test database isolation
        self._configure_db_isolation()

        # Set up security context
        self._setup_security_context()

        # Initialize version tracking for temporal tests
        self._init_version_tracking()

    def tearDown(self) -> None:
        """
        Clean up test environment and ensure proper resource cleanup.
        Resets test data, timestamps, and cleans up contexts.
        """
        # Clean up test data
        self.test_data.clear()
        self.test_timestamp = None

        # Clean up security context
        self._cleanup_security_context()

        # Clear version tracking data
        self._cleanup_version_tracking()

        super().tearDown()

    def _configure_db_isolation(self) -> None:
        """Configure database isolation for tests."""
        # Ensure each test uses a clean database state
        self.client.force_login = False
        self.client.logout()

    def _setup_security_context(self) -> None:
        """Set up security context for testing."""
        self.test_data['security'] = {
            'user_id': uuid.uuid4(),
            'role': 'test_user',
            'permissions': ['test_permission'],
            'session_id': uuid.uuid4()
        }

    def _cleanup_security_context(self) -> None:
        """Clean up security context after tests."""
        if 'security' in self.test_data:
            self.test_data['security'].clear()

    def _init_version_tracking(self) -> None:
        """Initialize version tracking for temporal data tests."""
        self.test_data['versions'] = {
            'current': 1,
            'history': [],
            'timestamps': {
                'created': self.test_timestamp,
                'modified': self.test_timestamp
            }
        }

    def _cleanup_version_tracking(self) -> None:
        """Clean up version tracking data."""
        if 'versions' in self.test_data:
            self.test_data['versions'].clear()

    def create_test_model(self, model_class: type[BaseModel], **kwargs) -> BaseModel:
        """
        Create a test model instance with proper timestamps and metadata.

        Args:
            model_class: The model class to instantiate
            **kwargs: Additional model fields

        Returns:
            BaseModel: Created test model instance
        """
        test_data = {
            'id': uuid.uuid4(),
            'created_at': self.test_timestamp,
            'updated_at': self.test_timestamp,
            'is_active': True,
            'metadata': {
                'test': True,
                'created_by': 'test_suite'
            },
            **kwargs
        }
        return model_class.objects.create(**test_data)

    def assert_timestamps_valid(self, obj: BaseModel) -> None:
        """
        Assert that model timestamps are valid.

        Args:
            obj: Model instance to validate
        """
        self.assertIsNotNone(obj.created_at)
        self.assertIsNotNone(obj.updated_at)
        self.assertGreaterEqual(obj.updated_at, obj.created_at)

    def assert_version_valid(self, obj: BaseModel, version: int = 1) -> None:
        """
        Assert that model version is valid.

        Args:
            obj: Model instance to validate
            version: Expected version number
        """
        if hasattr(obj, 'version'):
            self.assertEqual(obj.version, version)
            self.assertIsNotNone(obj.effective_from)
            if version > 1:
                self.assertIsNotNone(obj.previous_version)