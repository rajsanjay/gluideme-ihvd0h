"""
Comprehensive test suite for core serializer classes.
Tests validation, versioning, and audit logging functionality with enhanced security monitoring.

Version: 1.0
"""

# pytest v7.0+
import pytest
from freezegun import freeze_time  # v1.2+
from rest_framework.test import APITestCase  # v3.14+
from faker import Faker  # v8.0+
from django.utils import timezone
import uuid
from decimal import Decimal

# Internal imports
from apps.core.serializers import (
    BaseModelSerializer,
    VersionedModelSerializer,
    AuditModelSerializer
)
from apps.core.models import BaseModel, VersionedModel, AuditModel
from utils.exceptions import ValidationError

def pytest_configure(config):
    """Configure pytest with enhanced settings for serializer tests."""
    config.addinivalue_line(
        "markers", 
        "serializer: mark test as serializer test"
    )

class TestBaseModelSerializer(APITestCase):
    """Test cases for base model serializer functionality with enhanced validation coverage."""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Set up test environment with faker and test data."""
        self.faker = Faker()
        self.test_metadata = {
            "test_key": self.faker.word(),
            "test_value": self.faker.word()
        }
        self.serializer = BaseModelSerializer()

    def test_validate_base_fields(self):
        """Test validation of base model fields with comprehensive scenarios."""
        # Test valid data
        valid_data = {
            "is_active": True,
            "metadata": self.test_metadata
        }
        validated_data = self.serializer.validate(valid_data)
        assert validated_data["is_active"] is True
        assert validated_data["metadata"] == self.test_metadata

        # Test invalid metadata format
        with pytest.raises(ValidationError) as exc_info:
            self.serializer.validate({
                "metadata": "invalid_metadata"  # Should be dict
            })
        assert "metadata" in exc_info.value.validation_errors

        # Test sensitive data filtering
        sensitive_metadata = {
            "password": "secret123",
            "api_key": "sensitive_key",
            "normal_field": "safe_value"
        }
        validated_data = self.serializer.validate({"metadata": sensitive_metadata})
        assert "password" not in validated_data["metadata"]
        assert "api_key" not in validated_data["metadata"]
        assert validated_data["metadata"]["normal_field"] == "safe_value"

    def test_bulk_create(self):
        """Test bulk creation with validation and caching."""
        test_data = [
            {
                "is_active": True,
                "metadata": {"field": self.faker.word()}
            }
            for _ in range(3)
        ]

        # Test successful bulk creation
        instances = self.serializer.bulk_create(test_data)
        assert len(instances) == 3
        for instance in instances:
            assert instance.is_active is True
            assert "field" in instance.metadata

        # Test validation failure in bulk
        invalid_data = test_data + [{"metadata": "invalid"}]
        with pytest.raises(ValidationError) as exc_info:
            self.serializer.bulk_create(invalid_data)
        assert "metadata" in exc_info.value.validation_errors

class TestVersionedModelSerializer(APITestCase):
    """Test cases for versioned model serializer with time-frozen scenarios."""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Set up test environment with frozen time."""
        self.faker = Faker()
        self.serializer = VersionedModelSerializer()
        self.base_time = timezone.now()

    @freeze_time("2023-01-01 00:00:00")
    def test_create_version(self):
        """Test creation of new model versions with timestamp verification."""
        # Create initial version
        initial_data = {
            "is_active": True,
            "metadata": {"version": "1.0"},
            "effective_from": self.base_time
        }
        initial_version = self.serializer.create_version(initial_data)
        assert initial_version.version == 1
        assert initial_version.effective_from == self.base_time
        assert initial_version.effective_to is None

        # Create new version
        with freeze_time("2023-01-02 00:00:00"):
            new_data = {
                "metadata": {"version": "2.0"},
                "change_reason": "Update test"
            }
            new_version = self.serializer.create_version(new_data)
            assert new_version.version == 2
            assert new_version.previous_version == initial_version.id
            assert new_version.effective_from > initial_version.effective_from

    def test_version_validation(self):
        """Test version-specific validation rules."""
        # Test invalid effective date
        with pytest.raises(ValidationError) as exc_info:
            self.serializer.validate_version_transition({
                "effective_from": self.base_time - timezone.timedelta(days=1)
            })
        assert "effective_from" in exc_info.value.validation_errors

        # Test version chain validation
        with pytest.raises(ValidationError) as exc_info:
            self.serializer.create_version({
                "effective_from": self.base_time,
                "previous_version": uuid.uuid4()  # Invalid previous version
            })
        assert "version" in exc_info.value.validation_errors

class TestAuditModelSerializer(APITestCase):
    """Enhanced test cases for audit model serializer with comprehensive change tracking."""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Set up test environment with audit configuration."""
        self.faker = Faker()
        self.serializer = AuditModelSerializer()
        self.test_user_id = uuid.uuid4()
        self.context = {
            "request": type("Request", (), {
                "user": type("User", (), {"id": self.test_user_id}),
                "META": {
                    "REMOTE_ADDR": "127.0.0.1",
                    "HTTP_USER_AGENT": "test-agent"
                }
            })
        }
        self.serializer.context = self.context

    def test_audit_field_validation(self):
        """Test validation of audit fields with enhanced scenarios."""
        # Test valid audit data
        valid_data = {
            "created_by": self.test_user_id,
            "audit_metadata": {"action": "test"}
        }
        validated_data = self.serializer.validate(valid_data)
        assert validated_data["created_by"] == self.test_user_id
        assert validated_data["audit_metadata"]["action"] == "test"

        # Test missing user reference
        with pytest.raises(ValidationError) as exc_info:
            self.serializer.validate({"created_by": None})
        assert "created_by" in exc_info.value.validation_errors

        # Test invalid audit metadata
        with pytest.raises(ValidationError) as exc_info:
            self.serializer.validate({
                "audit_metadata": "invalid"  # Should be dict
            })
        assert "audit_metadata" in exc_info.value.validation_errors

    def test_change_log_tracking(self):
        """Comprehensive testing of change log generation and tracking."""
        # Create test instance
        instance = type("TestModel", (), {
            "change_log": [],
            "save": lambda *args, **kwargs: None
        })
        self.serializer.instance = instance

        # Test change logging
        changes = {
            "field1": {"old": "value1", "new": "value2"},
            "field2": {"old": 1, "new": 2}
        }
        change_entry = self.serializer.log_change(changes, "update")

        # Verify change log entry
        assert change_entry["change_type"] == "update"
        assert change_entry["user_id"] == str(self.test_user_id)
        assert change_entry["changes"] == changes
        assert "timestamp" in change_entry
        assert "ip_address" in change_entry["metadata"]
        assert "user_agent" in change_entry["metadata"]

    def test_bulk_audit_logging(self):
        """Test audit logging for bulk operations."""
        # Create bulk test data
        bulk_changes = [
            {"field": f"field{i}", "old": i, "new": i+1}
            for i in range(5)
        ]

        # Test bulk logging
        for changes in bulk_changes:
            instance = type("TestModel", (), {
                "change_log": [],
                "save": lambda *args, **kwargs: None
            })
            self.serializer.instance = instance
            change_entry = self.serializer.log_change(changes, "bulk_update")
            
            # Verify bulk audit entries
            assert change_entry["change_type"] == "bulk_update"
            assert change_entry["changes"] == changes
            assert len(instance.change_log) == 1