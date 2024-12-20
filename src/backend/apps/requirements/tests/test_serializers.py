"""
Comprehensive test suite for TransferRequirementSerializer.
Tests validation, versioning, and temporal aspects of transfer requirements.

Version: 1.0
"""

# pytest v7.0+
import pytest
from datetime import datetime, timedelta

# Django v4.2+
from django.db import transaction
from django.utils import timezone

# Django REST Framework v3.14+
from rest_framework.exceptions import ValidationError

# freezegun v1.2+
from freezegun import freeze_time

# Internal imports
from apps.requirements.serializers import (
    TransferRequirementSerializer,
    RequirementVersionSerializer
)
from apps.requirements.models import TransferRequirement
from apps.institutions.models import Institution
from apps.courses.models import Course

@pytest.mark.django_db
class TestTransferRequirementSerializer:
    """
    Comprehensive test suite for TransferRequirementSerializer covering validation,
    versioning, and temporal aspects.
    """

    @pytest.fixture
    def mock_institutions(self):
        """Create test institutions for validation."""
        source = Institution.objects.create(
            name="Test Community College",
            code="TCC",
            type="community_college",
            status="active",
            contact_info={
                "email": "contact@tcc.edu",
                "phone": "555-0100",
                "department": "Admissions"
            },
            address={
                "street": "123 College Ave",
                "city": "Test City",
                "state": "CA",
                "postal_code": "90210"
            }
        )
        target = Institution.objects.create(
            name="Test University",
            code="TU",
            type="university",
            status="active",
            contact_info={
                "email": "contact@tu.edu",
                "phone": "555-0200",
                "department": "Admissions"
            },
            address={
                "street": "456 University Dr",
                "city": "Test City",
                "state": "CA",
                "postal_code": "90211"
            }
        )
        return {"source": source, "target": target}

    @pytest.fixture
    def mock_courses(self, mock_institutions):
        """Create test courses for requirement validation."""
        courses = []
        for code in ["CS 101", "MATH 101", "PHYS 101"]:
            course = Course.objects.create(
                institution=mock_institutions["source"],
                code=code,
                name=f"Test {code}",
                credits=3.0,
                status="active",
                metadata={
                    "delivery_mode": "in_person",
                    "learning_outcomes": ["Test outcome"]
                }
            )
            courses.append(course)
        return courses

    @pytest.fixture
    def requirement_data(self, mock_institutions, mock_courses):
        """Create valid requirement test data."""
        return {
            "source_institution": mock_institutions["source"].id,
            "target_institution": mock_institutions["target"].id,
            "major_code": "CS",
            "rules": {
                "min_credits": 60,
                "courses": [{"code": c.code, "credits": c.credits} for c in mock_courses],
                "prerequisites": {
                    "CS 101": ["MATH 101"],
                    "PHYS 101": ["MATH 101"]
                }
            },
            "metadata": {
                "version_notes": "Initial version",
                "reviewer_id": "test-reviewer",
                "approval_date": timezone.now().isoformat()
            },
            "effective_date": timezone.now(),
            "status": "draft"
        }

    def test_requirement_validation_basic(self, requirement_data):
        """Test basic requirement validation."""
        serializer = TransferRequirementSerializer(data=requirement_data)
        assert serializer.is_valid(), f"Validation errors: {serializer.errors}"

        # Test invalid institution relationship
        invalid_data = requirement_data.copy()
        invalid_data["source_institution"] = invalid_data["target_institution"]
        serializer = TransferRequirementSerializer(data=invalid_data)
        with pytest.raises(ValidationError) as exc:
            serializer.is_valid(raise_exception=True)
        assert "institutions" in str(exc.value)

    def test_requirement_rules_validation(self, requirement_data):
        """Test comprehensive rules validation."""
        # Test missing required rule fields
        invalid_rules = requirement_data.copy()
        invalid_rules["rules"].pop("min_credits")
        serializer = TransferRequirementSerializer(data=invalid_rules)
        with pytest.raises(ValidationError) as exc:
            serializer.is_valid(raise_exception=True)
        assert "rules" in str(exc.value)

        # Test prerequisite cycle detection
        invalid_rules = requirement_data.copy()
        invalid_rules["rules"]["prerequisites"] = {
            "CS 101": ["MATH 101"],
            "MATH 101": ["CS 101"]
        }
        serializer = TransferRequirementSerializer(data=invalid_rules)
        with pytest.raises(ValidationError) as exc:
            serializer.is_valid(raise_exception=True)
        assert "prerequisites" in str(exc.value)

    @freeze_time("2024-01-01")
    def test_requirement_temporal_validation(self, requirement_data):
        """Test temporal validation aspects."""
        # Test invalid effective date
        invalid_data = requirement_data.copy()
        invalid_data["effective_date"] = (timezone.now() - timedelta(days=1)).isoformat()
        serializer = TransferRequirementSerializer(data=invalid_data)
        with pytest.raises(ValidationError) as exc:
            serializer.is_valid(raise_exception=True)
        assert "effective_date" in str(exc.value)

        # Test expiration date validation
        invalid_data = requirement_data.copy()
        invalid_data["expiration_date"] = timezone.now().isoformat()
        serializer = TransferRequirementSerializer(data=invalid_data)
        with pytest.raises(ValidationError) as exc:
            serializer.is_valid(raise_exception=True)
        assert "expiration_date" in str(exc.value)

    @pytest.mark.django_db(transaction=True)
    def test_requirement_version_chain_validation(self, requirement_data):
        """Test version chain integrity."""
        # Create initial version
        serializer = TransferRequirementSerializer(data=requirement_data)
        assert serializer.is_valid()
        requirement = serializer.save()

        # Create new version
        new_version_data = requirement_data.copy()
        new_version_data["rules"]["min_credits"] = 65
        new_version_data["metadata"]["version_notes"] = "Updated credits"
        new_version_data["effective_date"] = timezone.now() + timedelta(days=30)

        serializer = TransferRequirementSerializer(
            requirement,
            data=new_version_data,
            partial=True
        )
        assert serializer.is_valid()
        new_version = serializer.save()

        # Verify version chain
        assert new_version.version == requirement.version + 1
        assert new_version.previous_version == requirement.id
        assert requirement.effective_to == new_version.effective_from

    def test_requirement_bulk_validation(self, requirement_data, mock_institutions):
        """Test bulk requirement validation."""
        bulk_data = [
            requirement_data,
            {
                **requirement_data,
                "major_code": "MATH",
                "metadata": {
                    **requirement_data["metadata"],
                    "version_notes": "Math requirements"
                }
            }
        ]

        with transaction.atomic():
            valid_requirements = []
            for data in bulk_data:
                serializer = TransferRequirementSerializer(data=data)
                if serializer.is_valid():
                    valid_requirements.append(serializer.save())

        assert len(valid_requirements) == 2
        assert all(isinstance(req, TransferRequirement) for req in valid_requirements)

    def test_requirement_metadata_validation(self, requirement_data):
        """Test metadata validation."""
        # Test missing required metadata fields
        invalid_data = requirement_data.copy()
        invalid_data["metadata"].pop("reviewer_id")
        serializer = TransferRequirementSerializer(data=invalid_data)
        with pytest.raises(ValidationError) as exc:
            serializer.is_valid(raise_exception=True)
        assert "metadata" in str(exc.value)

        # Test invalid metadata format
        invalid_data = requirement_data.copy()
        invalid_data["metadata"] = "invalid"
        serializer = TransferRequirementSerializer(data=invalid_data)
        with pytest.raises(ValidationError) as exc:
            serializer.is_valid(raise_exception=True)
        assert "metadata" in str(exc.value)