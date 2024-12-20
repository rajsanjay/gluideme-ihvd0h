"""
Comprehensive unit tests for API v1 serializers validating data handling, validation logic,
and error scenarios with extensive coverage targeting 99.99% accuracy.

Version: 1.0
"""

from django.test import TestCase  # v4.2+
from django.utils import timezone  # v4.2+
from django.core.cache import cache  # v4.2+
from rest_framework.exceptions import ValidationError  # v3.14+
from freezegun import freeze_time  # v1.2+
from api.v1.serializers import (
    CourseSerializer,
    TransferRequirementSerializer,
    RequirementCourseSerializer
)
from apps.institutions.models import Institution
from apps.courses.models import Course
from apps.requirements.models import TransferRequirement
from decimal import Decimal
import uuid

class TestCourseSerializer(TestCase):
    """
    Comprehensive test cases for CourseSerializer validation and functionality
    including edge cases and performance scenarios.
    """
    
    def setUp(self):
        """Initialize test data and clear cache."""
        # Clear cache
        cache.clear()
        
        # Create test institution
        self.institution = Institution.objects.create(
            name="Test University",
            code="TEST",
            type="university",
            status="active",
            contact_info={
                "email": "test@test.edu",
                "phone": "123-456-7890",
                "department": "Admissions"
            },
            address={
                "street": "123 Test St",
                "city": "Test City",
                "state": "TS",
                "postal_code": "12345"
            }
        )
        
        # Create test course data
        self.valid_course_data = {
            "institution": self.institution.id,
            "code": "CS 101",
            "name": "Introduction to Programming",
            "description": "Basic programming concepts",
            "credits": Decimal("3.00"),
            "metadata": {
                "delivery_mode": "in_person",
                "learning_outcomes": ["outcome1", "outcome2"]
            },
            "status": "active",
            "valid_from": timezone.now()
        }
        
        # Initialize serializer
        self.serializer = CourseSerializer()

    def test_validate_credits(self):
        """Test credit validation with boundary values and precision."""
        # Test valid credits
        self.assertEqual(
            self.serializer.validate_credits(Decimal("3.00")),
            Decimal("3.00")
        )
        
        # Test minimum valid credits
        self.assertEqual(
            self.serializer.validate_credits(Decimal("0.25")),
            Decimal("0.25")
        )
        
        # Test maximum valid credits
        self.assertEqual(
            self.serializer.validate_credits(Decimal("12.00")),
            Decimal("12.00")
        )
        
        # Test invalid negative credits
        with self.assertRaises(ValidationError) as context:
            self.serializer.validate_credits(Decimal("-1.00"))
        self.assertIn("Credits must be greater than 0", str(context.exception))
        
        # Test invalid credit increment
        with self.assertRaises(ValidationError) as context:
            self.serializer.validate_credits(Decimal("3.33"))
        self.assertIn("Credits must be in increments of 0.25", str(context.exception))
        
        # Test credits exceeding maximum
        with self.assertRaises(ValidationError) as context:
            self.serializer.validate_credits(Decimal("13.00"))
        self.assertIn("Credits cannot exceed 12", str(context.exception))

    def test_validate_prerequisites(self):
        """Test prerequisite chain validation with complex scenarios."""
        # Create test prerequisite courses
        prereq1 = Course.objects.create(
            institution=self.institution,
            code="CS 100",
            name="Pre-Programming",
            credits=Decimal("3.00"),
            status="active"
        )
        
        prereq2 = Course.objects.create(
            institution=self.institution,
            code="MATH 101",
            name="Calculus I",
            credits=Decimal("4.00"),
            status="active"
        )
        
        # Test valid linear prerequisite chain
        valid_prereqs = [prereq1, prereq2]
        self.assertEqual(
            self.serializer.validate_prerequisites(valid_prereqs),
            valid_prereqs
        )
        
        # Test circular prerequisite detection
        circular_course = Course.objects.create(
            institution=self.institution,
            code="CS 102",
            name="Advanced Programming",
            credits=Decimal("3.00"),
            status="active"
        )
        circular_course.prerequisites.add(prereq1)
        prereq1.prerequisites.add(circular_course)
        
        with self.assertRaises(ValidationError) as context:
            self.serializer.validate_prerequisites([circular_course, prereq1])
        self.assertIn("Circular prerequisite dependency detected", str(context.exception))

    @freeze_time("2023-01-01 12:00:00")
    def test_validate_metadata(self):
        """Test course metadata validation with schema compliance."""
        # Test valid metadata
        valid_metadata = {
            "delivery_mode": "in_person",
            "learning_outcomes": ["outcome1", "outcome2"],
            "prerequisites_description": "Basic math skills required"
        }
        serializer = CourseSerializer(data={
            **self.valid_course_data,
            "metadata": valid_metadata
        })
        self.assertTrue(serializer.is_valid())
        
        # Test invalid delivery mode
        invalid_metadata = {
            **valid_metadata,
            "delivery_mode": "invalid_mode"
        }
        serializer = CourseSerializer(data={
            **self.valid_course_data,
            "metadata": invalid_metadata
        })
        self.assertFalse(serializer.is_valid())
        
        # Test missing required fields
        missing_fields_metadata = {
            "prerequisites_description": "Basic math skills required"
        }
        serializer = CourseSerializer(data={
            **self.valid_course_data,
            "metadata": missing_fields_metadata
        })
        self.assertFalse(serializer.is_valid())

    def test_serializer_performance(self):
        """Test serializer performance metrics and caching."""
        # Create test course
        course = Course.objects.create(**self.valid_course_data)
        
        # Test serialization with cache
        with self.assertNumQueries(1):  # Should only make 1 query due to caching
            serializer = CourseSerializer(course)
            data1 = serializer.data
            
        # Second serialization should use cache
        with self.assertNumQueries(0):
            serializer = CourseSerializer(course)
            data2 = serializer.data
            
        self.assertEqual(data1, data2)
        
        # Test bulk serialization performance
        courses = [
            Course.objects.create(
                institution=self.institution,
                code=f"CS {i}",
                name=f"Course {i}",
                credits=Decimal("3.00"),
                status="active"
            )
            for i in range(10)
        ]
        
        with self.assertNumQueries(1):  # Should batch query efficiently
            serializer = CourseSerializer(courses, many=True)
            data = serializer.data
            
        self.assertEqual(len(data), 10)

class TestTransferRequirementSerializer(TestCase):
    """
    Test cases for TransferRequirementSerializer with focus on validation 
    accuracy and version control.
    """
    
    def setUp(self):
        """Initialize test data and environment."""
        # Clear cache
        cache.clear()
        
        # Create test institutions
        self.source_institution = Institution.objects.create(
            name="Source University",
            code="SRC",
            type="university",
            status="active",
            contact_info={
                "email": "source@test.edu",
                "phone": "123-456-7890",
                "department": "Transfers"
            },
            address={
                "street": "123 Source St",
                "city": "Source City",
                "state": "SC",
                "postal_code": "12345"
            }
        )
        
        self.target_institution = Institution.objects.create(
            name="Target University",
            code="TGT",
            type="university",
            status="active",
            contact_info={
                "email": "target@test.edu",
                "phone": "123-456-7890",
                "department": "Transfers"
            },
            address={
                "street": "123 Target St",
                "city": "Target City",
                "state": "TC",
                "postal_code": "54321"
            }
        )
        
        # Create test requirement data
        self.valid_requirement_data = {
            "source_institution": self.source_institution.id,
            "target_institution": self.target_institution.id,
            "major_code": "CS",
            "title": "Computer Science Transfer",
            "type": "major",
            "rules": {
                "courses": ["CS 101", "CS 102"],
                "min_credits": 6,
                "prerequisites": {
                    "CS 102": ["CS 101"]
                }
            },
            "metadata": {
                "version_notes": "Initial version",
                "reviewer_id": str(uuid.uuid4()),
                "approval_date": timezone.now().isoformat()
            },
            "status": "draft"
        }

    def test_validate_rules(self):
        """Test requirement rules validation with complex scenarios."""
        serializer = TransferRequirementSerializer()
        
        # Test valid rules
        valid_rules = {
            "courses": ["CS 101", "CS 102"],
            "min_credits": 6,
            "prerequisites": {
                "CS 102": ["CS 101"]
            }
        }
        self.assertEqual(
            serializer.validate_rules(valid_rules),
            valid_rules
        )
        
        # Test missing required components
        invalid_rules = {
            "courses": ["CS 101"]
        }
        with self.assertRaises(ValidationError) as context:
            serializer.validate_rules(invalid_rules)
        self.assertIn("Missing required rule components", str(context.exception))
        
        # Test circular prerequisite detection
        circular_rules = {
            "courses": ["CS 101", "CS 102"],
            "min_credits": 6,
            "prerequisites": {
                "CS 101": ["CS 102"],
                "CS 102": ["CS 101"]
            }
        }
        with self.assertRaises(ValidationError) as context:
            serializer.validate_rules(circular_rules)
        self.assertIn("Circular prerequisite chain detected", str(context.exception))

    @freeze_time("2023-01-01 12:00:00")
    def test_validate_version(self):
        """Test version control validation with temporal integrity."""
        # Create initial requirement
        requirement = TransferRequirement.objects.create(
            **self.valid_requirement_data
        )
        
        # Test valid version increment
        new_version_data = {
            **self.valid_requirement_data,
            "version": requirement.version + 1,
            "metadata": {
                **self.valid_requirement_data["metadata"],
                "version_notes": "Updated version"
            }
        }
        serializer = TransferRequirementSerializer(data=new_version_data)
        self.assertTrue(serializer.is_valid())
        
        # Test invalid version decrement
        invalid_version_data = {
            **self.valid_requirement_data,
            "version": requirement.version - 1
        }
        serializer = TransferRequirementSerializer(data=invalid_version_data)
        self.assertFalse(serializer.is_valid())
        
        # Test version conflict
        with freeze_time("2023-01-02 12:00:00"):
            conflict_data = {
                **self.valid_requirement_data,
                "version": requirement.version
            }
            serializer = TransferRequirementSerializer(data=conflict_data)
            self.assertFalse(serializer.is_valid())

    def test_temporal_validation(self):
        """Test temporal aspects of requirements with date validation."""
        # Test valid date range
        valid_data = {
            **self.valid_requirement_data,
            "effective_date": timezone.now(),
            "expiration_date": timezone.now() + timezone.timedelta(days=365)
        }
        serializer = TransferRequirementSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        
        # Test invalid date range
        invalid_data = {
            **self.valid_requirement_data,
            "effective_date": timezone.now(),
            "expiration_date": timezone.now() - timezone.timedelta(days=1)
        }
        serializer = TransferRequirementSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        
        # Test overlapping versions
        requirement = TransferRequirement.objects.create(**valid_data)
        overlap_data = {
            **valid_data,
            "effective_date": requirement.effective_date + timezone.timedelta(days=1),
            "expiration_date": requirement.expiration_date + timezone.timedelta(days=1)
        }
        serializer = TransferRequirementSerializer(data=overlap_data)
        self.assertFalse(serializer.is_valid())