"""
Test suite for transfer requirement and requirement course models.
Implements comprehensive testing of validation accuracy, versioning, and core functionality.

Version: 1.0
"""

import pytest  # v7.0+
from freezegun import freeze_time  # v1.2+
from django.core.exceptions import ValidationError  # v4.2+
from django.utils import timezone  # v4.2+
from unittest.mock import patch  # v3.8+
from decimal import Decimal
from apps.requirements.models import TransferRequirement
from apps.courses.models import Course
from apps.institutions.models import Institution
from typing import List, Dict, Any

class RequirementTestCase:
    """
    Base test case class for requirement model tests with enhanced validation metrics.
    """
    def setUp(self) -> None:
        """
        Set up test fixtures with comprehensive validation tracking.
        """
        # Create test institutions
        self.source_institution = Institution.objects.create(
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
                "postal_code": "90001"
            }
        )
        
        self.target_institution = Institution.objects.create(
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
                "street": "456 University Blvd",
                "city": "Test City",
                "state": "CA",
                "postal_code": "90002"
            }
        )

        # Create test courses
        self.test_courses = []
        course_data = [
            ("CS 101", "Intro to Programming", 3.0),
            ("CS 102", "Data Structures", 3.0),
            ("MATH 101", "Calculus I", 4.0),
            ("MATH 102", "Calculus II", 4.0)
        ]
        
        for code, name, credits in course_data:
            course = Course.objects.create(
                institution=self.source_institution,
                code=code,
                name=name,
                credits=Decimal(str(credits)),
                status="active",
                metadata={
                    "delivery_mode": "in_person",
                    "learning_outcomes": ["outcome1", "outcome2"]
                }
            )
            self.test_courses.append(course)

        # Initialize validation metrics
        self.validation_metrics = {
            "total_validations": 0,
            "successful_validations": 0,
            "failed_validations": 0,
            "false_positives": 0,
            "false_negatives": 0
        }

    def tearDown(self) -> None:
        """
        Clean up test data and reset metrics.
        """
        Course.objects.all().delete()
        Institution.objects.all().delete()
        TransferRequirement.objects.all().delete()
        self.validation_metrics = {}

@pytest.mark.django_db
class TestTransferRequirement(RequirementTestCase):
    """
    Comprehensive test suite for TransferRequirement model.
    """
    
    def test_requirement_creation(self) -> None:
        """Test basic requirement creation with validation."""
        requirement = TransferRequirement.objects.create(
            source_institution=self.source_institution,
            target_institution=self.target_institution,
            major_code="CS",
            title="Computer Science Transfer",
            type="major",
            rules={
                "courses": ["CS 101", "CS 102", "MATH 101"],
                "min_credits": 10.0,
                "prerequisites": {}
            },
            metadata={
                "version_notes": "Initial version",
                "reviewer_id": "test-reviewer",
                "approval_date": timezone.now().isoformat()
            },
            status="published"
        )
        
        assert requirement.pk is not None
        assert requirement.version == 1
        assert requirement.is_active()[0] is True

    @pytest.mark.django_db
    @freeze_time("2024-01-01")
    def test_requirement_versioning(self) -> None:
        """Test temporal versioning of requirements."""
        # Create initial version
        requirement = TransferRequirement.objects.create(
            source_institution=self.source_institution,
            target_institution=self.target_institution,
            major_code="CS",
            title="Computer Science Transfer",
            type="major",
            rules={
                "courses": ["CS 101", "CS 102"],
                "min_credits": 6.0,
                "prerequisites": {}
            },
            metadata={
                "version_notes": "Initial version",
                "reviewer_id": "test-reviewer",
                "approval_date": "2024-01-01"
            }
        )
        
        # Create new version
        updated_rules = {
            "courses": ["CS 101", "CS 102", "MATH 101"],
            "min_credits": 9.0,
            "prerequisites": {}
        }
        
        with freeze_time("2024-02-01"):
            new_version = requirement.create_new_version(
                data={"rules": updated_rules},
                reason="Added MATH 101 requirement"
            )
            
            # Verify version increments
            assert new_version.version == 2
            assert new_version.previous_version == requirement.pk
            
            # Test version retrieval by date
            assert requirement.get_version_at(
                timezone.datetime(2024, 1, 15)
            ).version == 1
            
            assert new_version.get_version_at(
                timezone.datetime(2024, 2, 15)
            ).version == 2

    @pytest.mark.django_db
    def test_validation_accuracy(self) -> None:
        """Test requirement validation accuracy meets 99.99% target."""
        # Create test requirement
        requirement = TransferRequirement.objects.create(
            source_institution=self.source_institution,
            target_institution=self.target_institution,
            major_code="CS",
            title="Computer Science Transfer",
            type="major",
            rules={
                "courses": ["CS 101", "CS 102", "MATH 101"],
                "min_credits": 10.0,
                "prerequisites": {
                    "CS 102": ["CS 101"],
                    "MATH 102": ["MATH 101"]
                }
            },
            status="published"
        )

        # Test cases for validation
        test_cases = [
            {
                "courses": self.test_courses[:3],  # Valid case
                "expected_valid": True
            },
            {
                "courses": self.test_courses[:1],  # Missing required courses
                "expected_valid": False
            },
            {
                "courses": [self.test_courses[1]],  # Missing prerequisite
                "expected_valid": False
            }
        ]

        # Run validation tests
        for case in test_cases:
            result = requirement.validate_courses(case["courses"])
            self.validation_metrics["total_validations"] += 1
            
            if result["valid"] == case["expected_valid"]:
                self.validation_metrics["successful_validations"] += 1
            else:
                self.validation_metrics["failed_validations"] += 1
                if result["valid"] and not case["expected_valid"]:
                    self.validation_metrics["false_positives"] += 1
                elif not result["valid"] and case["expected_valid"]:
                    self.validation_metrics["false_negatives"] += 1

        # Calculate accuracy
        total = self.validation_metrics["total_validations"]
        successful = self.validation_metrics["successful_validations"]
        accuracy = (successful / total) * 100 if total > 0 else 0

        # Assert 99.99% accuracy target
        assert accuracy >= 99.99, f"Validation accuracy {accuracy}% below target 99.99%"
        assert self.validation_metrics["false_positives"] == 0, "Found false positive validations"
        assert self.validation_metrics["false_negatives"] == 0, "Found false negative validations"

    def test_requirement_rules_validation(self) -> None:
        """Test comprehensive validation of requirement rules."""
        with pytest.raises(ValidationError) as exc_info:
            TransferRequirement.objects.create(
                source_institution=self.source_institution,
                target_institution=self.target_institution,
                major_code="CS",
                title="Invalid Requirement",
                type="major",
                rules={
                    "courses": ["INVALID 101"],  # Invalid course code
                    "min_credits": -1.0,  # Invalid credits
                    "prerequisites": {
                        "CS 102": ["CS 102"]  # Circular dependency
                    }
                }
            )

        assert "validation" in str(exc_info.value)
        assert "course code" in str(exc_info.value)
        assert "credits" in str(exc_info.value)
        assert "Circular dependency" in str(exc_info.value)