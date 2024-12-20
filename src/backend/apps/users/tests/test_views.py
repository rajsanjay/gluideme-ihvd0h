"""
Comprehensive test suite for user management views in the Transfer Requirements Management System.
Tests authentication, authorization, security, and performance requirements.

Version: 1.0
"""

# Django REST Framework v3.14+
from rest_framework.test import APITestCase
from rest_framework import status

# JWT Token handling v5.2+
from rest_framework_simplejwt.tokens import AccessToken

# Performance timing
import time

# Internal imports
from apps.users.models import User, ROLE_CHOICES
from apps.users.views import UserViewSet
from apps.institutions.models import Institution
from utils.exceptions import ValidationError

class UserViewSetTests(APITestCase):
    """
    Test suite for UserViewSet validating role-based access control,
    data security, and performance requirements.
    """

    def setUp(self):
        """Initialize test environment with users of different roles and institutions."""
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

        # Create test users for each role
        self.test_users = {}
        self.test_tokens = {}
        
        for role, _ in ROLE_CHOICES:
            user = User.objects.create_user(
                email=f"{role}@example.com",
                password="SecurePass123!",
                first_name=f"Test",
                last_name=role.title(),
                role=role,
                institution=self.institution1 if role != 'admin' else None
            )
            self.test_users[role] = user
            self.test_tokens[role] = str(AccessToken.for_user(user))

        # Create additional users for cross-institution tests
        self.other_institution_user = User.objects.create_user(
            email="other@example.com",
            password="SecurePass123!",
            first_name="Other",
            last_name="User",
            role="counselor",
            institution=self.institution2
        )

    def test_list_users_admin(self):
        """Test admin access to full user list with performance check."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.test_tokens["admin"]}')
        
        start_time = time.time()
        response = self.client.get('/api/v1/users/')
        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Validate performance requirement (<500ms)
        self.assertLess(response_time, 500, "API response time exceeds 500ms requirement")
        
        # Validate response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= len(ROLE_CHOICES))
        
        # Verify sensitive data protection
        for user in response.data:
            self.assertNotIn('password', user)
            self.assertNotIn('security_settings', user)

    def test_list_users_institution_admin(self):
        """Test institution admin access restrictions."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.test_tokens["institution_admin"]}'
        )
        
        response = self.client.get('/api/v1/users/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify only institution users are returned
        for user in response.data:
            self.assertEqual(
                user['institution'], 
                str(self.institution1.id)
            )

    def test_list_users_counselor(self):
        """Test counselor access restrictions to students only."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.test_tokens["counselor"]}'
        )
        
        response = self.client.get('/api/v1/users/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify only students and guests are visible
        for user in response.data:
            self.assertIn(user['role'], ['student', 'guest'])
            self.assertEqual(
                user['institution'], 
                str(self.institution1.id)
            )

    def test_user_detail_access(self):
        """Test user detail access based on roles."""
        test_cases = [
            ('admin', 'student', True),  # Admin can view any user
            ('institution_admin', 'student', True),  # Institution admin can view institution students
            ('institution_admin', 'admin', False),  # Institution admin cannot view admins
            ('counselor', 'student', True),  # Counselor can view students
            ('counselor', 'admin', False),  # Counselor cannot view admins
            ('student', 'student', False),  # Student cannot view other students
        ]

        for viewer_role, target_role, should_access in test_cases:
            self.client.credentials(
                HTTP_AUTHORIZATION=f'Bearer {self.test_tokens[viewer_role]}'
            )
            
            response = self.client.get(
                f'/api/v1/users/{self.test_users[target_role].id}/'
            )
            
            expected_status = status.HTTP_200_OK if should_access else status.HTTP_403_FORBIDDEN
            self.assertEqual(
                response.status_code, 
                expected_status,
                f"{viewer_role} -> {target_role} access test failed"
            )

    def test_create_user_permissions(self):
        """Test user creation permissions and validation."""
        new_user_data = {
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'student',
            'institution': str(self.institution1.id)
        }

        # Test admin creation
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.test_tokens["admin"]}'
        )
        response = self.client.post('/api/v1/users/', new_user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Test institution admin creation restrictions
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.test_tokens["institution_admin"]}'
        )
        new_user_data['email'] = 'another@example.com'
        new_user_data['role'] = 'admin'  # Should be rejected
        response = self.client.post('/api/v1/users/', new_user_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Test counselor creation permission denied
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.test_tokens["counselor"]}'
        )
        response = self.client.post('/api/v1/users/', new_user_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_user_permissions(self):
        """Test user update permissions and validation."""
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }

        # Test self-update
        student = self.test_users['student']
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.test_tokens["student"]}'
        )
        response = self.client.patch(
            f'/api/v1/users/{student.id}/',
            update_data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test unauthorized update
        other_student = User.objects.create_user(
            email='other.student@example.com',
            password='SecurePass123!',
            first_name='Other',
            last_name='Student',
            role='student',
            institution=self.institution1
        )
        response = self.client.patch(
            f'/api/v1/users/{other_student.id}/',
            update_data
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_activate_deactivate_user(self):
        """Test user activation and deactivation permissions."""
        student = self.test_users['student']

        # Test admin deactivation
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.test_tokens["admin"]}'
        )
        response = self.client.post(f'/api/v1/users/{student.id}/deactivate/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test institution admin activation
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.test_tokens["institution_admin"]}'
        )
        response = self.client.post(f'/api/v1/users/{student.id}/activate/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test unauthorized activation
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.test_tokens["counselor"]}'
        )
        response = self.client.post(f'/api/v1/users/{student.id}/activate/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_performance_requirements(self):
        """Test API performance requirements."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.test_tokens["admin"]}'
        )

        # Test list performance
        start_time = time.time()
        response = self.client.get('/api/v1/users/')
        list_time = (time.time() - start_time) * 1000

        self.assertLess(list_time, 500, "List operation exceeds 500ms requirement")

        # Test detail performance
        start_time = time.time()
        response = self.client.get(f'/api/v1/users/{self.test_users["student"].id}/')
        detail_time = (time.time() - start_time) * 1000

        self.assertLess(detail_time, 500, "Detail operation exceeds 500ms requirement")

    def test_security_headers(self):
        """Test security headers in responses."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.test_tokens["admin"]}'
        )
        
        response = self.client.get('/api/v1/users/')
        
        # Verify security headers
        self.assertIn('X-Content-Type-Options', response.headers)
        self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
        self.assertIn('X-Frame-Options', response.headers)
        self.assertIn('Content-Security-Policy', response.headers)

class UserRegistrationTests(APITestCase):
    """Test suite for user registration including security and validation."""

    def setUp(self):
        """Set up test data for registration scenarios."""
        self.institution = Institution.objects.create(
            name="Test University",
            code="TU",
            type="university",
            status="active"
        )
        
        self.valid_user_data = {
            'email': 'test@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'student',
            'institution': str(self.institution.id)
        }

    def test_secure_password_requirements(self):
        """Test password security requirements."""
        test_cases = [
            ('short', 'Password too short'),
            ('nodigits', 'Password must contain digits'),
            ('NO_LOWERCASE!123', 'Password must contain lowercase'),
            ('no_uppercase123', 'Password must contain uppercase'),
            ('NoSpecialChars123', 'Password must contain special characters'),
            ('Password123!', 'Password too common')
        ]

        for password, expected_error in test_cases:
            data = self.valid_user_data.copy()
            data['password'] = password
            data['confirm_password'] = password

            response = self.client.post('/api/v1/users/register/', data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('password', response.data['validation_errors'])
            self.assertIn(expected_error.lower(), 
                         response.data['validation_errors']['password'].lower())

    def test_email_validation(self):
        """Test email validation requirements."""
        test_cases = [
            ('invalid_email', 'Invalid email format'),
            ('test@invalid', 'Invalid domain'),
            ('@example.com', 'Invalid email format'),
            ('', 'Email required')
        ]

        for email, expected_error in test_cases:
            data = self.valid_user_data.copy()
            data['email'] = email

            response = self.client.post('/api/v1/users/register/', data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('email', response.data['validation_errors'])

    def test_duplicate_email_prevention(self):
        """Test prevention of duplicate email registration."""
        # Create first user
        response = self.client.post('/api/v1/users/register/', self.valid_user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Attempt duplicate registration
        response = self.client.post('/api/v1/users/register/', self.valid_user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data['validation_errors'])
        self.assertIn('already exists', response.data['validation_errors']['email'])

    def test_registration_rate_limiting(self):
        """Test registration rate limiting."""
        for _ in range(5):  # Attempt multiple registrations
            data = self.valid_user_data.copy()
            data['email'] = f"test{_}@example.com"
            response = self.client.post('/api/v1/users/register/', data)

        # Next attempt should be rate limited
        data = self.valid_user_data.copy()
        data['email'] = "final@example.com"
        response = self.client.post('/api/v1/users/register/', data)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)