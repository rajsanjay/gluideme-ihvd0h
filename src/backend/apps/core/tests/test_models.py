"""
Comprehensive unit tests for core Django models.
Tests cover model functionality, versioning, audit logging, and data integrity.

Version: 1.0
"""

import pytest
from django.utils import timezone  # v4.2+
from django.db import transaction  # v4.2+
from freezegun import freeze_time  # v1.2+
import uuid
from datetime import timedelta
from decimal import Decimal

from apps.core.models import BaseModel, VersionedModel, AuditModel
from utils.exceptions import ValidationError

# Test Models for concrete implementation
class TestBaseModelImpl(BaseModel):
    class Meta:
        app_label = 'core'

class TestVersionedModelImpl(VersionedModel):
    class Meta:
        app_label = 'core'

class TestAuditModelImpl(AuditModel):
    class Meta:
        app_label = 'core'

@pytest.fixture
def base_model():
    return TestBaseModelImpl.objects.create(
        metadata={'test_key': 'test_value'}
    )

@pytest.fixture
def versioned_model():
    return TestVersionedModelImpl.objects.create(
        metadata={'test_key': 'test_value'},
        version_metadata={'initial': True}
    )

@pytest.fixture
def audit_model():
    return TestAuditModelImpl.objects.create(
        metadata={'test_key': 'test_value'},
        created_by=uuid.uuid4()
    )

class TestBaseModel:
    """Test suite for BaseModel functionality."""

    @pytest.mark.django_db
    def test_auto_fields_creation(self, base_model):
        """Test automatic field population on model creation."""
        assert isinstance(base_model.id, uuid.UUID)
        assert base_model.created_at is not None
        assert base_model.updated_at is not None
        assert base_model.is_active is True
        assert isinstance(base_model.metadata, dict)
        assert base_model.metadata['test_key'] == 'test_value'

    @pytest.mark.django_db
    def test_soft_delete_cascade(self, base_model):
        """Test soft deletion with metadata updates."""
        # Create related models to test cascade
        child_model = TestBaseModelImpl.objects.create(
            metadata={'parent_id': str(base_model.id)}
        )

        # Perform soft delete
        assert base_model.soft_delete() is True
        base_model.refresh_from_db()
        
        # Verify soft delete
        assert base_model.is_active is False
        assert 'deleted_at' in base_model.metadata
        assert timezone.parse_datetime(base_model.metadata['deleted_at'])

    @pytest.mark.django_db
    def test_metadata_validation(self, base_model):
        """Test metadata validation and updates."""
        # Test invalid metadata
        with pytest.raises(ValidationError) as exc:
            base_model.metadata = "invalid"  # Should be dict
            base_model.save()
        assert "validation" in str(exc.value)

        # Test valid metadata update
        base_model.metadata = {'updated': True}
        base_model.save()
        base_model.refresh_from_db()
        assert base_model.metadata['updated'] is True

    @pytest.mark.django_db
    def test_bulk_operations(self):
        """Test bulk create and update operations."""
        # Bulk create
        models = [
            TestBaseModelImpl(metadata={'bulk_id': i})
            for i in range(5)
        ]
        TestBaseModelImpl.objects.bulk_create(models)
        assert TestBaseModelImpl.objects.count() == 5

        # Bulk update
        with transaction.atomic():
            for model in TestBaseModelImpl.objects.all():
                model.metadata['bulk_updated'] = True
                model.save()

class TestVersionedModel:
    """Test suite for VersionedModel functionality."""

    @pytest.mark.django_db
    @freeze_time("2024-01-01 12:00:00")
    def test_version_creation(self, versioned_model):
        """Test version creation and chain management."""
        initial_version = versioned_model.version
        
        # Create new version
        new_version = versioned_model.create_new_version(
            data={'metadata': {'updated': True}},
            reason="Test update",
            effective_date=timezone.now() + timedelta(days=1)
        )

        # Verify version chain
        assert new_version.version == initial_version + 1
        assert new_version.previous_version == versioned_model.id
        assert new_version.effective_from > versioned_model.effective_from
        assert versioned_model.effective_to == new_version.effective_from

    @pytest.mark.django_db
    def test_temporal_integrity(self, versioned_model):
        """Test temporal data integrity and validation."""
        # Try to create overlapping version
        with pytest.raises(ValidationError) as exc:
            versioned_model.create_new_version(
                data={},
                reason="Overlap test",
                effective_date=versioned_model.effective_from - timedelta(days=1)
            )
        assert "temporal" in str(exc.value)

        # Test version retrieval at timestamp
        future_time = timezone.now() + timedelta(days=2)
        version_at_time = versioned_model.get_version_at(future_time)
        assert version_at_time is None

    @pytest.mark.django_db
    def test_version_metadata(self, versioned_model):
        """Test version metadata handling and validation."""
        # Update with invalid metadata
        with pytest.raises(ValidationError):
            versioned_model.version_metadata = []  # Should be dict
            versioned_model.save()

        # Valid metadata update
        versioned_model.version_metadata = {
            'change_type': 'major',
            'reviewed_by': str(uuid.uuid4())
        }
        versioned_model.save()
        assert 'change_type' in versioned_model.version_metadata

class TestAuditModel:
    """Test suite for AuditModel functionality."""

    @pytest.mark.django_db
    def test_audit_logging(self, audit_model):
        """Test comprehensive audit logging functionality."""
        user_id = uuid.uuid4()
        
        # Log a change
        audit_model.log_change(
            action="update",
            changes={'field': 'new_value'},
            user_id=user_id,
            category="data_update"
        )

        # Verify audit log
        assert len(audit_model.change_log) == 1
        latest_change = audit_model.change_log[-1]
        assert latest_change['action'] == "update"
        assert latest_change['user_id'] == str(user_id)
        assert latest_change['category'] == "data_update"

    @pytest.mark.django_db
    def test_audit_security(self, audit_model):
        """Test audit security and access controls."""
        # Test unauthorized change
        with pytest.raises(ValidationError) as exc:
            audit_model.log_change(
                action="sensitive_update",
                changes={'sensitive_field': 'value'},
                user_id=None,  # Missing user
                category="security"
            )
        assert "user_id" in str(exc.value)

        # Test valid security audit
        user_id = uuid.uuid4()
        audit_model.log_change(
            action="security_update",
            changes={'security_level': 'high'},
            user_id=user_id,
            category="security"
        )
        assert audit_model.change_category == "security"

    @pytest.mark.django_db
    def test_audit_performance(self, audit_model):
        """Test audit logging performance with high volume."""
        user_id = uuid.uuid4()
        
        # Generate multiple audit entries
        for i in range(100):
            audit_model.log_change(
                action=f"bulk_test_{i}",
                changes={'iteration': i},
                user_id=user_id,
                category="performance_test"
            )

        # Verify log integrity
        assert len(audit_model.change_log) == 100
        assert all(log['category'] == "performance_test" 
                  for log in audit_model.change_log)

def pytest_configure(config):
    """Configure pytest environment for model testing."""
    # Configure test database settings
    config.addinivalue_line(
        "markers", "django_db: mark test to use db transaction"
    )