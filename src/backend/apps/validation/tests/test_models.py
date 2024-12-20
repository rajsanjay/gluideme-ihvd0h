"""
Comprehensive unit tests for validation app models including ValidationRecord and ValidationCache models.
Implements test coverage for real-time validation engine, accuracy requirements, caching behavior, 
and temporal validation scenarios.

Version: 1.0
"""

from django.test import TestCase  # v4.2+
from django.utils import timezone  # v4.2+
from freezegun import freeze_time  # v1.2+
from apps.validation.models import ValidationRecord, ValidationCache
from apps.courses.models import Course
from apps.requirements.models import TransferRequirement
from apps.institutions.models import Institution
from decimal import Decimal
import uuid

def setUpModule():
    """
    Enhanced module level setup for tests with comprehensive fixtures.
    """
    # Configure test database
    global test_institutions
    test_institutions = {
        'source': Institution.objects.create(
            name='Test Community College',
            code='TCC',
            type='community_college',
            status='active',
            contact_info={'email': 'test@tcc.edu', 'phone': '555-0100', 'department': 'Registrar'},
            address={'street': '123 Test St', 'city': 'Test City', 'state': 'CA', 'postal_code': '90210'}
        ),
        'target': Institution.objects.create(
            name='Test University',
            code='TU',
            type='university',
            status='active',
            contact_info={'email': 'test@tu.edu', 'phone': '555-0200', 'department': 'Admissions'},
            address={'street': '456 Test Ave', 'city': 'Test City', 'state': 'CA', 'postal_code': '90211'}
        )
    }

def tearDownModule():
    """
    Comprehensive module level cleanup.
    """
    # Clean up test data
    Institution.objects.all().delete()
    Course.objects.all().delete()
    TransferRequirement.objects.all().delete()
    ValidationRecord.objects.all().delete()
    ValidationCache.objects.all().delete()

class ValidationRecordTests(TestCase):
    """
    Comprehensive test cases for ValidationRecord model including accuracy metrics 
    and temporal validation.
    """
    maxDiff = None

    def setUp(self):
        """
        Enhanced test setup with comprehensive test data.
        """
        # Create test course
        self.course = Course.objects.create(
            institution=test_institutions['source'],
            code='CS 101',
            name='Introduction to Programming',
            credits=Decimal('3.00'),
            status='active',
            metadata={
                'delivery_mode': 'in_person',
                'learning_outcomes': ['outcome1', 'outcome2']
            }
        )

        # Create test requirement
        self.requirement = TransferRequirement.objects.create(
            source_institution=test_institutions['source'],
            target_institution=test_institutions['target'],
            major_code='CS',
            title='Computer Science Requirements',
            type='major',
            rules={
                'courses': ['CS 101'],
                'min_credits': 3.0,
                'prerequisites': {}
            },
            status='published'
        )

        # Create test validation record
        self.validation_record = ValidationRecord.objects.create(
            requirement=self.requirement,
            course=self.course,
            status='pending',
            metadata={'progress': 0}
        )

    def test_validation_record_creation(self):
        """
        Test validation record creation with accuracy metrics.
        """
        record = ValidationRecord.objects.create(
            requirement=self.requirement,
            course=self.course,
            metadata={'initial_check': True}
        )

        self.assertEqual(record.status, 'pending')
        self.assertIsNone(record.accuracy_score)
        self.assertTrue(record.metadata.get('initial_check'))
        self.assertIsNotNone(record.validated_at)
        self.assertIsNone(record.valid_until)

    def test_validate_method(self):
        """
        Comprehensive test of validate method functionality.
        """
        # Perform validation
        results = self.validation_record.validate()

        # Verify validation results
        self.assertIsInstance(results, dict)
        self.assertTrue('course_valid' in results)
        self.assertTrue('requirement_valid' in results)
        self.assertTrue('accuracy_score' in results)
        self.assertTrue('validation_timestamp' in results)

        # Check validation progress tracking
        self.assertEqual(self.validation_record.metadata['progress'], 100)
        self.assertEqual(self.validation_record.status, 'valid')
        self.assertIsNotNone(self.validation_record.valid_until)
        self.assertEqual(self.validation_record.accuracy_score, Decimal('100.00'))

    @freeze_time("2023-01-01 12:00:00")
    def test_is_valid_method(self):
        """
        Enhanced testing of is_valid method with temporal validation.
        """
        # Setup validation record with known state
        self.validation_record.status = 'valid'
        self.validation_record.accuracy_score = Decimal('99.99')
        self.validation_record.validated_at = timezone.now()
        self.validation_record.valid_until = timezone.now() + timezone.timedelta(days=1)
        self.validation_record.save()

        # Test current validity
        self.assertTrue(self.validation_record.is_valid())

        # Test future validity
        future_date = timezone.now() + timezone.timedelta(hours=23)
        self.assertTrue(self.validation_record.is_valid(date=future_date))

        # Test expired validity
        expired_date = timezone.now() + timezone.timedelta(days=2)
        self.assertFalse(self.validation_record.is_valid(date=expired_date))

        # Test accuracy threshold
        self.assertTrue(self.validation_record.is_valid(min_accuracy=99.99))
        self.assertFalse(self.validation_record.is_valid(min_accuracy=100.00))

class ValidationCacheTests(TestCase):
    """
    Comprehensive test cases for ValidationCache model with performance metrics.
    """
    maxDiff = None

    def setUp(self):
        """
        Enhanced cache test setup.
        """
        # Create test course and requirement
        self.course = Course.objects.create(
            institution=test_institutions['source'],
            code='MATH 101',
            name='Calculus I',
            credits=Decimal('4.00'),
            status='active'
        )

        self.requirement = TransferRequirement.objects.create(
            source_institution=test_institutions['source'],
            target_institution=test_institutions['target'],
            major_code='MATH',
            title='Mathematics Requirements',
            type='major',
            status='published'
        )

        # Create test cache entry
        self.cache_entry = ValidationCache.objects.create(
            requirement=self.requirement,
            course=self.course,
            cache_key=f"validation:{self.requirement.pk}:{self.course.pk}",
            results={'valid': True},
            expires_at=timezone.now() + timezone.timedelta(days=1)
        )

    def test_cache_creation(self):
        """
        Test cache entry creation with performance metrics.
        """
        cache_entry = ValidationCache.objects.create(
            requirement=self.requirement,
            course=self.course,
            cache_key=f"validation:{uuid.uuid4()}",
            results={'test': True},
            expires_at=timezone.now() + timezone.timedelta(hours=24)
        )

        self.assertEqual(cache_entry.hit_count, 0)
        self.assertIsNotNone(cache_entry.created_at)
        self.assertTrue(cache_entry.is_valid())
        self.assertDictEqual(cache_entry.results, {'test': True})

    def test_is_valid_method(self):
        """
        Comprehensive cache validity testing.
        """
        # Test valid cache
        self.assertTrue(self.cache_entry.is_valid())
        self.assertEqual(self.cache_entry.hit_count, 1)

        # Test expired cache
        self.cache_entry.expires_at = timezone.now() - timezone.timedelta(minutes=1)
        self.cache_entry.save()
        self.assertFalse(self.cache_entry.is_valid())

        # Test inactive requirement
        self.requirement.status = 'archived'
        self.requirement.save()
        self.assertFalse(self.cache_entry.is_valid())

    def test_refresh_method(self):
        """
        Enhanced cache refresh testing.
        """
        new_results = {
            'valid': True,
            'updated': True,
            'timestamp': timezone.now().isoformat()
        }

        # Refresh cache entry
        self.cache_entry.refresh(new_results)

        # Verify refresh
        self.assertDictEqual(self.cache_entry.results, new_results)
        self.assertEqual(self.cache_entry.hit_count, 0)
        self.assertTrue(
            timezone.now() < self.cache_entry.expires_at <= 
            timezone.now() + timezone.timedelta(days=1)
        )