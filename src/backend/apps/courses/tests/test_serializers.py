"""
Comprehensive test suite for Course and CourseEquivalency serializers.
Implements extensive validation testing with 99.99% accuracy requirement.

Version: 1.0
"""

from django.test import TestCase  # v4.2+
from django.utils import timezone  # v4.2+
from rest_framework.exceptions import ValidationError  # v3.14+
from faker import Faker  # v8.0+
from freezegun import freeze_time  # v1.2+
from decimal import Decimal
from apps.courses.serializers import CourseSerializer, CourseEquivalencySerializer
from apps.courses.models import Course, CourseEquivalency
from apps.institutions.models import Institution
from django.core.cache import cache
import uuid

class TestCourseSerializer(TestCase):
    """
    Comprehensive test suite for CourseSerializer validation and functionality.
    Ensures 99.99% accuracy in course data validation.
    """
    maxDiff = None

    def setUp(self):
        """Set up test data before each test case."""
        self.faker = Faker()
        
        # Create test institution
        self.institution = Institution.objects.create(
            name="Test University",
            code="TEST",
            type="university",
            status="active",
            contact_info={"email": "test@test.edu", "phone": "123-456-7890", "department": "Admissions"},
            address={"street": "123 Test St", "city": "Test City", "state": "TS", "postal_code": "12345"}
        )

        # Set up valid course data
        self.valid_course_data = {
            'institution': self.institution.id,
            'code': 'CS 101',
            'name': 'Introduction to Computer Science',
            'description': 'Basic programming concepts',
            'credits': Decimal('3.00'),
            'metadata': {
                'delivery_mode': 'in_person',
                'learning_outcomes': ['Understand basic programming']
            },
            'status': 'active',
            'valid_from': timezone.now()
        }

        # Clear cache
        cache.clear()

    def test_valid_course_serialization(self):
        """Test successful serialization of valid course data."""
        serializer = CourseSerializer(data=self.valid_course_data)
        self.assertTrue(serializer.is_valid(raise_exception=True))
        
        course = serializer.save()
        self.assertEqual(course.code, 'CS 101')
        self.assertEqual(course.credits, Decimal('3.00'))
        self.assertEqual(course.validation_status, 'valid')

    def test_course_code_validation(self):
        """Test comprehensive course code validation rules."""
        invalid_codes = [
            ('CS101', 'Invalid format'),
            ('CS 1O1', 'Invalid number'),
            ('XX 101', 'Invalid department'),
            ('CS 99999999', 'Number too large'),
            ('', 'Empty code'),
            ('CS 101A B', 'Extra characters')
        ]

        for code, error_type in invalid_codes:
            data = self.valid_course_data.copy()
            data['code'] = code
            serializer = CourseSerializer(data=data)
            with self.assertRaises(ValidationError) as context:
                serializer.is_valid(raise_exception=True)
            self.assertIn('code', str(context.exception))

    def test_credits_validation(self):
        """Test credit value validation with precise decimal handling."""
        invalid_credits = [
            (-1.0, 'Negative credits'),
            (0.0, 'Zero credits'),
            (13.0, 'Exceeds maximum'),
            (3.33, 'Invalid increment'),
            ('abc', 'Non-numeric value')
        ]

        for credits, error_type in invalid_credits:
            data = self.valid_course_data.copy()
            data['credits'] = credits
            serializer = CourseSerializer(data=data)
            with self.assertRaises(ValidationError) as context:
                serializer.is_valid(raise_exception=True)
            self.assertIn('credits', str(context.exception))

    def test_metadata_validation(self):
        """Test metadata schema validation and required fields."""
        invalid_metadata = [
            ({}, 'Missing required fields'),
            ({'delivery_mode': 'invalid'}, 'Invalid delivery mode'),
            ({'delivery_mode': 'online'}, 'Missing learning outcomes'),
            ({'learning_outcomes': []}, 'Empty learning outcomes')
        ]

        for metadata, error_type in invalid_metadata:
            data = self.valid_course_data.copy()
            data['metadata'] = metadata
            serializer = CourseSerializer(data=data)
            with self.assertRaises(ValidationError) as context:
                serializer.is_valid(raise_exception=True)
            self.assertIn('metadata', str(context.exception))

    @freeze_time("2023-01-01")
    def test_date_validation(self):
        """Test temporal validation with frozen time."""
        # Test invalid date ranges
        data = self.valid_course_data.copy()
        data['valid_to'] = timezone.now()
        data['valid_from'] = timezone.now() + timezone.timedelta(days=1)
        
        serializer = CourseSerializer(data=data)
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn('valid_to', str(context.exception))

class TestCourseEquivalencySerializer(TestCase):
    """
    Comprehensive test suite for CourseEquivalencySerializer validation and functionality.
    Ensures 99.99% accuracy in equivalency validation.
    """
    maxDiff = None

    def setUp(self):
        """Set up test data before each test case."""
        self.faker = Faker()
        
        # Create test institutions
        self.source_institution = Institution.objects.create(
            name="Source University",
            code="SRC",
            type="university",
            status="active",
            contact_info={"email": "source@test.edu", "phone": "123-456-7890", "department": "Admissions"},
            address={"street": "123 Source St", "city": "Test City", "state": "TS", "postal_code": "12345"}
        )
        
        self.target_institution = Institution.objects.create(
            name="Target University",
            code="TGT",
            type="university",
            status="active",
            contact_info={"email": "target@test.edu", "phone": "123-456-7890", "department": "Admissions"},
            address={"street": "123 Target St", "city": "Test City", "state": "TS", "postal_code": "12345"}
        )

        # Create test courses
        self.source_course = Course.objects.create(
            institution=self.source_institution,
            code="CS 101",
            name="Intro to Programming",
            credits=Decimal("3.00"),
            metadata={
                'delivery_mode': 'in_person',
                'learning_outcomes': ['Basic programming']
            }
        )

        self.target_course = Course.objects.create(
            institution=self.target_institution,
            code="COMP 101",
            name="Programming Fundamentals",
            credits=Decimal("3.00"),
            metadata={
                'delivery_mode': 'in_person',
                'learning_outcomes': ['Programming basics']
            }
        )

        # Set up valid equivalency data
        self.valid_equivalency_data = {
            'source_course_id': self.source_course.id,
            'target_course_id': self.target_course.id,
            'effective_date': timezone.now(),
            'metadata': {
                'approval_date': timezone.now().isoformat(),
                'approved_by': str(uuid.uuid4())
            },
            'notes': 'Standard equivalency'
        }

        # Clear cache
        cache.clear()

    def test_valid_equivalency_serialization(self):
        """Test successful serialization of valid equivalency data."""
        serializer = CourseEquivalencySerializer(data=self.valid_equivalency_data)
        self.assertTrue(serializer.is_valid(raise_exception=True))
        
        equivalency = serializer.save()
        self.assertEqual(equivalency.source_course, self.source_course)
        self.assertEqual(equivalency.target_course, self.target_course)

    def test_same_institution_validation(self):
        """Test validation preventing equivalency within same institution."""
        same_inst_course = Course.objects.create(
            institution=self.source_institution,
            code="CS 102",
            name="Another Course",
            credits=Decimal("3.00"),
            metadata={
                'delivery_mode': 'in_person',
                'learning_outcomes': ['Learning']
            }
        )

        data = self.valid_equivalency_data.copy()
        data['target_course_id'] = same_inst_course.id
        
        serializer = CourseEquivalencySerializer(data=data)
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn('Source and target courses must be from different institutions', 
                     str(context.exception))

    def test_credit_compatibility(self):
        """Test credit difference validation between courses."""
        incompatible_course = Course.objects.create(
            institution=self.target_institution,
            code="COMP 201",
            name="Advanced Course",
            credits=Decimal("5.00"),
            metadata={
                'delivery_mode': 'in_person',
                'learning_outcomes': ['Advanced topics']
            }
        )

        data = self.valid_equivalency_data.copy()
        data['target_course_id'] = incompatible_course.id
        
        serializer = CourseEquivalencySerializer(data=data)
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn('Credit difference between courses exceeds maximum allowed', 
                     str(context.exception))

    @freeze_time("2023-01-01")
    def test_date_range_validation(self):
        """Test temporal validation for equivalency dates."""
        # Test invalid date ranges
        data = self.valid_equivalency_data.copy()
        data['effective_date'] = timezone.now()
        data['expiration_date'] = timezone.now() - timezone.timedelta(days=1)
        
        serializer = CourseEquivalencySerializer(data=data)
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn('expiration_date', str(context.exception))

    def test_audit_log_generation(self):
        """Test audit log creation for equivalency changes."""
        serializer = CourseEquivalencySerializer(
            data=self.valid_equivalency_data,
            context={'request': type('Request', (), {'user': type('User', (), {'id': uuid.uuid4()})()})()}
        )
        self.assertTrue(serializer.is_valid(raise_exception=True))
        
        equivalency = serializer.save()
        self.assertIsNotNone(equivalency.audit_log)
        self.assertEqual(len(equivalency.audit_log), 1)
        self.assertEqual(equivalency.audit_log[0]['action'], 'create')