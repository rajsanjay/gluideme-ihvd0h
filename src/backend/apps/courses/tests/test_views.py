"""
Comprehensive test suite for course management API views.
Tests CRUD operations, permissions, search, and performance requirements.

Version: 1.0
"""

# Django REST Framework imports - v3.14+
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch, Mock
import time

# Local imports
from apps.courses.models import Course, CourseEquivalency
from apps.courses.views import CourseViewSet, CourseEquivalencyViewSet
from apps.institutions.models import Institution
from apps.users.models import User

class CourseViewSetTests(APITestCase):
    """
    Comprehensive test cases for course management API endpoints including CRUD operations,
    permissions, search, and performance.
    """
    maxDiff = None

    def setUp(self):
        """Set up test data and authentication for all roles."""
        # Create test institutions
        self.institution1 = Institution.objects.create(
            name="Test University 1",
            code="TU1",
            type="university",
            status="active"
        )
        self.institution2 = Institution.objects.create(
            name="Test College 2",
            code="TC2",
            type="community_college",
            status="active"
        )

        # Create test users with different roles
        self.admin_user = User.objects.create_superuser(
            email="admin@test.com",
            password="testpass123"
        )
        self.institution_admin = User.objects.create_user(
            email="inst_admin@test.com",
            password="testpass123",
            institution=self.institution1,
            role="institution_admin"
        )
        self.counselor = User.objects.create_user(
            email="counselor@test.com",
            password="testpass123",
            institution=self.institution1,
            role="counselor"
        )
        self.student = User.objects.create_user(
            email="student@test.com",
            password="testpass123",
            role="student"
        )

        # Create test courses
        self.course1 = Course.objects.create(
            institution=self.institution1,
            code="CS 101",
            name="Introduction to Programming",
            description="Basic programming concepts",
            credits="3.00",
            status="active",
            metadata={
                "delivery_mode": "in_person",
                "learning_outcomes": ["outcome1", "outcome2"]
            }
        )
        self.course2 = Course.objects.create(
            institution=self.institution2,
            code="MATH 101",
            name="Calculus I",
            description="Introduction to calculus",
            credits="4.00",
            status="active",
            metadata={
                "delivery_mode": "hybrid",
                "learning_outcomes": ["outcome1", "outcome2"]
            }
        )

        # Set up course equivalency
        self.equivalency = CourseEquivalency.objects.create(
            source_course=self.course1,
            target_course=self.course2,
            validation_status="approved"
        )

        # Set up API client
        self.client = self.client_class()
        self.base_url = reverse('course-list')

    def test_list_courses(self):
        """Test course listing with different user roles and pagination."""
        # Test admin access - should see all courses
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

        # Test institution admin access - should only see own institution's courses
        self.client.force_authenticate(user=self.institution_admin)
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['code'], 'CS 101')

        # Test counselor access - should see permitted courses
        self.client.force_authenticate(user=self.counselor)
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

        # Test student access - should see active courses only
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(all(c['status'] == 'active' for c in response.data['results']))

        # Test search functionality
        response = self.client.get(f"{self.base_url}?search=programming")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['code'], 'CS 101')

        # Test performance requirements
        start_time = time.time()
        response = self.client.get(self.base_url)
        response_time = time.time() - start_time
        self.assertLess(response_time, 0.5)  # 500ms max response time

    def test_create_course(self):
        """Test course creation with validation and permissions."""
        course_data = {
            "institution": self.institution1.id,
            "code": "CS 102",
            "name": "Data Structures",
            "description": "Advanced data structures",
            "credits": "3.00",
            "status": "active",
            "metadata": {
                "delivery_mode": "in_person",
                "learning_outcomes": ["outcome1", "outcome2"]
            }
        }

        # Test unauthorized access
        self.client.force_authenticate(user=self.student)
        response = self.client.post(self.base_url, course_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Test institution admin creation
        self.client.force_authenticate(user=self.institution_admin)
        response = self.client.post(self.base_url, course_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['code'], 'CS 102')

        # Test duplicate course code
        response = self.client.post(self.base_url, course_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test invalid data validation
        invalid_data = course_data.copy()
        invalid_data['credits'] = "invalid"
        response = self.client.post(self.base_url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_course(self):
        """Test course update functionality with validation."""
        update_url = reverse('course-detail', args=[self.course1.id])
        update_data = {
            "name": "Updated Programming Course",
            "description": "Updated description",
            "credits": "4.00"
        }

        # Test unauthorized update
        self.client.force_authenticate(user=self.student)
        response = self.client.patch(update_url, update_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Test authorized update
        self.client.force_authenticate(user=self.institution_admin)
        response = self.client.patch(update_url, update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Programming Course')

        # Test invalid update
        invalid_update = {"credits": "invalid"}
        response = self.client.patch(update_url, invalid_update)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_search_courses(self):
        """Test advanced course search functionality."""
        # Test full-text search
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(f"{self.base_url}?search=programming")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

        # Test filtering
        response = self.client.get(
            f"{self.base_url}?institution={self.institution1.id}&credits=3.00"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

        # Test sorting
        response = self.client.get(f"{self.base_url}?ordering=-credits")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['credits'], '4.00')

        # Test search performance
        start_time = time.time()
        response = self.client.get(f"{self.base_url}?search=calculus")
        response_time = time.time() - start_time
        self.assertLess(response_time, 0.2)  # 200ms max search time

class CourseEquivalencyViewSetTests(APITestCase):
    """Test cases for course equivalency management with advanced validation."""
    maxDiff = None

    def setUp(self):
        """Set up test data for equivalency tests."""
        # Set up base test data
        self.institution1 = Institution.objects.create(
            name="Test University 1",
            code="TU1",
            type="university"
        )
        self.institution2 = Institution.objects.create(
            name="Test College 2",
            code="TC2",
            type="community_college"
        )

        self.course1 = Course.objects.create(
            institution=self.institution1,
            code="CS 101",
            name="Programming I",
            credits="3.00",
            status="active"
        )
        self.course2 = Course.objects.create(
            institution=self.institution2,
            code="CSC 101",
            name="Intro Programming",
            credits="3.00",
            status="active"
        )

        self.admin_user = User.objects.create_superuser(
            email="admin@test.com",
            password="testpass123"
        )
        self.client.force_authenticate(user=self.admin_user)

    def test_equivalency_validation(self):
        """Test complex equivalency validation rules."""
        equivalency_data = {
            "source_course": self.course1.id,
            "target_course": self.course2.id,
            "effective_date": timezone.now().isoformat(),
            "metadata": {
                "validation_method": "faculty_review",
                "reviewer_notes": "Content matches 90%"
            }
        }

        # Test valid equivalency creation
        response = self.client.post(reverse('courseequivalency-list'), equivalency_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Test duplicate equivalency
        response = self.client.post(reverse('courseequivalency-list'), equivalency_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test invalid course combination
        invalid_data = equivalency_data.copy()
        invalid_data['source_course'] = self.course1.id
        invalid_data['target_course'] = self.course1.id
        response = self.client.post(reverse('courseequivalency-list'), invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test date validation
        invalid_date_data = equivalency_data.copy()
        invalid_date_data['effective_date'] = "invalid_date"
        response = self.client.post(reverse('courseequivalency-list'), invalid_date_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)