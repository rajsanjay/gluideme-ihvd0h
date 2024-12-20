"""
Comprehensive test suite for validation app views implementing test coverage for course validation endpoints,
cache operations, and permission controls with enhanced accuracy metrics and performance monitoring.

Version: 1.0
"""

from django.urls import reverse  # v4.2+
from django.utils import timezone  # v4.2+
from rest_framework import status  # v3.14+
from rest_framework.test import APITestCase  # v3.14+
from apps.validation.views import ValidationRecordViewSet, ValidationCacheViewSet
from apps.validation.models import ValidationRecord, ValidationCache
from apps.courses.models import Course
from apps.requirements.models import TransferRequirement
from apps.institutions.models import Institution
from decimal import Decimal
import json
import uuid

class ValidationRecordViewSetTests(APITestCase):
    """
    Comprehensive test suite for validation record management views with enhanced accuracy metrics.
    Tests validation endpoints, bulk operations, and accuracy requirements.
    """

    def setUp(self):
        """
        Enhanced test case setup with comprehensive test data.
        Creates test institutions, courses, requirements, and validation records.
        """
        # Create test institutions
        self.source_institution = Institution.objects.create(
            name="Test Community College",
            code="TCC",
            type="community_college",
            status="active"
        )
        self.target_institution = Institution.objects.create(
            name="Test University",
            code="TU",
            type="university",
            status="active"
        )

        # Create test courses
        self.test_courses = []
        for i in range(3):
            course = Course.objects.create(
                institution=self.source_institution,
                code=f"CS {100 + i}",
                name=f"Test Course {i}",
                credits=Decimal("3.00"),
                status="active"
            )
            self.test_courses.append(course)

        # Create test requirement
        self.test_requirement = TransferRequirement.objects.create(
            source_institution=self.source_institution,
            target_institution=self.target_institution,
            major_code="CS",
            title="Computer Science Requirements",
            type="major",
            rules={
                "courses": [course.code for course in self.test_courses],
                "min_credits": 9,
                "prerequisites": {}
            },
            status="published"
        )

        # Create test users with different roles
        self.admin_user = self._create_user("admin")
        self.institution_admin = self._create_user("institution_admin")
        self.counselor = self._create_user("counselor")
        self.student = self._create_user("student")

        # Set up test data
        self.test_data = {
            "course_id": str(self.test_courses[0].id),
            "requirement_id": str(self.test_requirement.id)
        }

        # Initialize validation metrics
        self.validation_metrics = {
            "total_validations": 0,
            "successful_validations": 0,
            "failed_validations": 0,
            "cache_hits": 0
        }

    def _create_user(self, role):
        """Helper method to create test users with specific roles."""
        return {
            "id": uuid.uuid4(),
            "role": role,
            "is_active": True
        }

    def test_validate_course_success(self):
        """
        Test successful course validation with accuracy metrics.
        Verifies 99.99% accuracy requirement is met.
        """
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('validation-validate-course')
        
        response = self.client.post(url, self.test_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['valid'])
        self.assertGreaterEqual(response.data['accuracy_score'], Decimal('99.99'))
        
        # Verify validation record creation
        validation_record = ValidationRecord.objects.get(
            course_id=self.test_data['course_id'],
            requirement_id=self.test_data['requirement_id']
        )
        self.assertEqual(validation_record.status, 'valid')
        self.assertGreaterEqual(validation_record.accuracy_score, Decimal('99.99'))

    def test_validate_courses_bulk(self):
        """
        Test bulk course validation operations with performance monitoring.
        Verifies efficient processing of multiple courses.
        """
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('validation-bulk-validate-courses')
        
        bulk_data = {
            "course_ids": [str(course.id) for course in self.test_courses],
            "requirement_id": str(self.test_requirement.id)
        }
        
        response = self.client.post(url, bulk_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('validation_timestamp', response.data)
        self.assertIn('total_courses', response.data)
        self.assertEqual(response.data['total_courses'], len(self.test_courses))
        
        # Verify bulk processing metrics
        self.assertIn('metrics', response.data)
        self.assertIn('processing_time', response.data['metrics'])
        self.assertIn('cache_hits', response.data['metrics'])

    def test_validation_permissions(self):
        """
        Test role-based access control for validation operations.
        Verifies proper permission enforcement.
        """
        url = reverse('validation-validate-course')
        
        # Test unauthorized access
        response = self.client.post(url, self.test_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test student access
        self.client.force_authenticate(user=self.student)
        response = self.client.post(url, self.test_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test counselor access
        self.client.force_authenticate(user=self.counselor)
        response = self.client.post(url, self.test_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_validation_accuracy_threshold(self):
        """
        Test validation accuracy meets 99.99% requirement.
        Verifies high accuracy standards are maintained.
        """
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('validation-validate-course')
        
        # Perform multiple validations
        for course in self.test_courses:
            data = {
                "course_id": str(course.id),
                "requirement_id": str(self.test_requirement.id)
            }
            response = self.client.post(url, data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Verify accuracy threshold
            validation_record = ValidationRecord.objects.get(
                course_id=data['course_id'],
                requirement_id=data['requirement_id']
            )
            self.assertGreaterEqual(
                validation_record.accuracy_score,
                Decimal('99.99'),
                "Validation accuracy below required threshold"
            )

class ValidationCacheViewSetTests(APITestCase):
    """
    Test suite for validation cache management with performance monitoring.
    Tests cache operations and metrics tracking.
    """

    def setUp(self):
        """
        Test case setup for cache testing with performance metrics initialization.
        """
        self.admin_user = self._create_user("admin")
        self.cache_metrics = {
            "hit_ratio": 0.0,
            "miss_ratio": 0.0,
            "total_requests": 0
        }
        
        # Create test cache entries
        self.test_cache = ValidationCache.objects.create(
            requirement=self.test_requirement,
            course=self.test_courses[0],
            cache_key=f"validation:{self.test_requirement.id}:{self.test_courses[0].id}",
            results={"valid": True, "accuracy_score": 100.0},
            expires_at=timezone.now() + timezone.timedelta(hours=1)
        )

    def _create_user(self, role):
        """Helper method to create test users with specific roles."""
        return {
            "id": uuid.uuid4(),
            "role": role,
            "is_active": True
        }

    def test_cache_hit_ratio(self):
        """
        Test cache performance metrics and hit ratio calculation.
        Verifies efficient cache utilization.
        """
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('validation-cache-metrics')
        
        # Perform cache operations
        for _ in range(10):
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
        # Verify cache metrics
        response = self.client.get(url)
        self.assertIn('hit_ratio', response.data)
        self.assertIn('total_requests', response.data)
        self.assertGreaterEqual(response.data['hit_ratio'], 0.8)

    def test_cache_expiry_handling(self):
        """
        Test cache entry expiration and cleanup.
        Verifies proper cache maintenance.
        """
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('validation-clear-cache')
        
        # Create expired cache entry
        expired_cache = ValidationCache.objects.create(
            requirement=self.test_requirement,
            course=self.test_courses[1],
            cache_key=f"validation:{self.test_requirement.id}:{self.test_courses[1].id}",
            results={"valid": True},
            expires_at=timezone.now() - timezone.timedelta(hours=1)
        )
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify expired cache cleanup
        self.assertFalse(
            ValidationCache.objects.filter(id=expired_cache.id).exists()
        )
        self.assertTrue(
            ValidationCache.objects.filter(id=self.test_cache.id).exists()
        )