"""
Comprehensive test suite for API v1 views implementing extensive test coverage for 
transfer requirements management system endpoints.

Version: 1.0
"""

from rest_framework.test import APITestCase  # v3.14+
from rest_framework import status
from django.urls import reverse
from django.utils import timezone
from django.core.cache import cache
import pytest
import uuid
from decimal import Decimal
from typing import Dict, List, Optional

from api.v1.views import TransferRequirementViewSet, CourseViewSet
from apps.institutions.models import Institution
from apps.courses.models import Course, CourseEquivalency
from apps.requirements.models import TransferRequirement
from utils.exceptions import ValidationError, NotFoundError

@pytest.mark.django_db
class TestTransferRequirementViewSet(APITestCase):
    """
    Comprehensive test cases for transfer requirement API endpoints including
    validation, authorization, and error handling.
    """
    fixtures = [
        'test_users.json',
        'test_institutions.json',
        'test_courses.json',
        'test_requirements.json'
    ]

    def setUp(self):
        """Set up test environment with different user roles and authentication."""
        # Create test users with different roles
        self.admin_user = self.create_test_user('admin')
        self.institution_admin = self.create_test_user('institution_admin', 'inst_1')
        self.counselor = self.create_test_user('counselor', 'inst_1')
        self.student = self.create_test_user('student')

        # Generate authentication tokens
        self.admin_token = self.generate_test_jwt(self.admin_user)
        self.inst_admin_token = self.generate_test_jwt(self.institution_admin)
        self.counselor_token = self.generate_test_jwt(self.counselor)
        self.student_token = self.generate_test_jwt(self.student)

        # Set up test data
        self.source_institution = Institution.objects.get(code='INST1')
        self.target_institution = Institution.objects.get(code='INST2')
        
        # Clear cache
        cache.clear()

    def test_list_requirements(self):
        """Test GET request to list requirements with filtering and pagination."""
        # Test unauthenticated access
        url = reverse('api:v1:requirements-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test authenticated access with admin
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)

        # Test filtering by institution
        response = self.client.get(
            url, 
            {'source_institution': self.source_institution.id}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for req in response.data['results']:
            self.assertEqual(req['source_institution'], str(self.source_institution.id))

        # Test search functionality
        response = self.client.get(url, {'search': 'Computer Science'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test pagination
        response = self.client.get(url, {'page': 1, 'page_size': 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(response.data['results']), 10)

    def test_create_requirement(self):
        """Test POST request to create requirement with validation."""
        url = reverse('api:v1:requirements-list')
        requirement_data = {
            'source_institution': str(self.source_institution.id),
            'target_institution': str(self.target_institution.id),
            'major_code': 'CS',
            'title': 'Computer Science Transfer Requirements',
            'type': 'major',
            'rules': {
                'courses': [
                    {'code': 'CS101', 'credits': 3},
                    {'code': 'CS102', 'credits': 3}
                ],
                'min_credits': 6,
                'prerequisites': {
                    'CS102': ['CS101']
                }
            },
            'status': 'draft',
            'effective_date': timezone.now().isoformat()
        }

        # Test unauthenticated access
        response = self.client.post(url, requirement_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test with institution admin
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.inst_admin_token}')
        response = self.client.post(url, requirement_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['major_code'], 'CS')

        # Test validation errors
        invalid_data = requirement_data.copy()
        invalid_data['rules']['min_credits'] = -1
        response = self.client.post(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test duplicate creation
        response = self.client.post(url, requirement_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_validate_courses(self):
        """Test course validation with complex rule sets."""
        requirement = TransferRequirement.objects.first()
        url = reverse('api:v1:requirements-validate-courses', args=[requirement.id])

        # Create test courses
        course1 = Course.objects.create(
            institution=self.source_institution,
            code='CS101',
            name='Intro to Programming',
            credits=Decimal('3.0')
        )
        course2 = Course.objects.create(
            institution=self.source_institution,
            code='CS102',
            name='Data Structures',
            credits=Decimal('3.0')
        )

        validation_data = {
            'courses': [str(course1.id), str(course2.id)]
        }

        # Test unauthenticated access
        response = self.client.post(url, validation_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test with student access
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token}')
        response = self.client.post(url, validation_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('valid', response.data)
        self.assertIn('completion_percentage', response.data)

        # Test invalid course IDs
        invalid_data = {
            'courses': [str(uuid.uuid4())]
        }
        response = self.client.post(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test prerequisite validation
        course2.prerequisites.add(course1)
        response = self.client.post(url, validation_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('prerequisite_issues', response.data)

@pytest.mark.django_db
class TestCourseViewSet(APITestCase):
    """Test cases for course management API endpoints with comprehensive validation."""
    fixtures = [
        'test_users.json',
        'test_institutions.json',
        'test_courses.json'
    ]

    def setUp(self):
        """Set up test environment for course testing."""
        # Create test users
        self.admin_user = self.create_test_user('admin')
        self.institution_admin = self.create_test_user('institution_admin', 'inst_1')

        # Generate tokens
        self.admin_token = self.generate_test_jwt(self.admin_user)
        self.inst_admin_token = self.generate_test_jwt(self.institution_admin)

        # Set up test data
        self.institution = Institution.objects.first()
        self.course = Course.objects.create(
            institution=self.institution,
            code='MATH101',
            name='Calculus I',
            credits=Decimal('4.0')
        )

        # Clear cache
        cache.clear()

    def test_check_transfer_validity(self):
        """Test course transfer validity checking."""
        url = reverse('api:v1:courses-check-transfer-validity', args=[self.course.id])
        target_institution = Institution.objects.exclude(id=self.institution.id).first()

        validity_data = {
            'target_institution': str(target_institution.id)
        }

        # Test unauthenticated access
        response = self.client.post(url, validity_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test with institution admin
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.inst_admin_token}')
        response = self.client.post(url, validity_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('valid', response.data)
        self.assertIn('reasons', response.data)

        # Test invalid target institution
        invalid_data = {
            'target_institution': str(uuid.uuid4())
        }
        response = self.client.post(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test course not found
        invalid_url = reverse('api:v1:courses-check-transfer-validity', args=[uuid.uuid4()])
        response = self.client.post(invalid_url, validity_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

def create_test_user(role: str, institution_id: Optional[str] = None) -> 'User':
    """Helper function to create test users with specific roles and permissions."""
    from django.contrib.auth import get_user_model
    User = get_user_model()

    user = User.objects.create_user(
        username=f'test_{role}_{uuid.uuid4().hex[:8]}',
        email=f'{role}@test.com',
        password='testpass123'
    )

    if role == 'admin':
        user.is_staff = True
        user.is_superuser = True
    elif role in ('institution_admin', 'counselor'):
        if institution_id:
            user.institutions.add(institution_id)
    
    user.save()
    return user

def generate_test_jwt(user: 'User') -> str:
    """Helper function to generate JWT tokens for test authentication."""
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)