"""
Comprehensive test suite for core view classes including BaseViewSet, VersionedViewSet, and AuditViewSet.
Implements extensive testing for API endpoints, authentication, permissions, versioning, audit logging.

Version: 1.0
"""

# pytest v7.0+
import pytest
from freezegun import freeze_time  # v1.2+
from rest_framework.test import APITestCase  # v3.14+
from rest_framework import status  # v3.14+
from rest_framework_simplejwt.authentication import JWTAuthentication  # v5.2+
from django.utils import timezone
from django.contrib.auth import get_user_model
import uuid
import json

# Internal imports
from apps.core.views import BaseViewSet, VersionedViewSet, AuditViewSet
from apps.core.models import BaseModel, VersionedModel
from utils.exceptions import ValidationError, AuthenticationError, PermissionDeniedError

User = get_user_model()

def pytest_configure(config):
    """Configure pytest environment for view testing."""
    config.addinivalue_line(
        "markers", 
        "django_db: mark test to use db access"
    )

@pytest.mark.django_db
class TestBaseViewSet(APITestCase):
    """
    Comprehensive test cases for BaseViewSet functionality including 
    authentication, permissions, and error handling.
    """
    
    def setUp(self):
        """Set up test case with authentication and test data."""
        super().setUp()
        
        # Create test users with different roles
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123!'
        )
        self.institution_admin = User.objects.create_user(
            username='inst_admin',
            email='inst_admin@example.com',
            password='inst123!',
            role='institution_admin'
        )
        self.counselor = User.objects.create_user(
            username='counselor',
            email='counselor@example.com',
            password='counselor123!',
            role='counselor'
        )
        self.student = User.objects.create_user(
            username='student',
            email='student@example.com',
            password='student123!',
            role='student'
        )

        # Set up JWT authentication
        self.auth = JWTAuthentication()
        self.base_url = '/api/v1/test/'
        self.test_data = {
            'name': 'Test Resource',
            'description': 'Test description',
            'metadata': {'key': 'value'}
        }

    def test_authentication_required(self):
        """Test authentication requirements and JWT validation."""
        # Test unauthenticated request
        response = self.client.get(self.base_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test with invalid token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        response = self.client.get(self.base_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test with expired token
        with freeze_time("2024-01-01"):
            token = self.auth.get_token(self.admin_user)
        
        with freeze_time("2024-02-01"):
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
            response = self.client.get(self.base_url)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test with valid token
        token = self.auth.get_token(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(self.base_url)
        assert response.status_code == status.HTTP_200_OK

    def test_role_based_access(self):
        """Test role-based authorization controls."""
        admin_token = self.auth.get_token(self.admin_user)
        inst_admin_token = self.auth.get_token(self.institution_admin)
        counselor_token = self.auth.get_token(self.counselor)
        student_token = self.auth.get_token(self.student)

        # Test admin access
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token}')
        response = self.client.post(self.base_url, self.test_data)
        assert response.status_code == status.HTTP_201_CREATED

        # Test institution admin access
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {inst_admin_token}')
        response = self.client.get(f"{self.base_url}institution/")
        assert response.status_code == status.HTTP_200_OK

        # Test counselor access restrictions
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {counselor_token}')
        response = self.client.delete(f"{self.base_url}1/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Test student access restrictions
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {student_token}')
        response = self.client.put(f"{self.base_url}1/", self.test_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_error_handling(self):
        """Test comprehensive error handling scenarios."""
        token = self.auth.get_token(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        # Test validation error
        invalid_data = {'name': ''}
        response = self.client.post(self.base_url, invalid_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'validation_errors' in response.data

        # Test not found error
        response = self.client.get(f"{self.base_url}{uuid.uuid4()}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

        # Test server error handling
        with pytest.raises(Exception):
            response = self.client.post(f"{self.base_url}error/", self.test_data)
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

@pytest.mark.django_db
class TestVersionedViewSet(APITestCase):
    """
    Test cases for VersionedViewSet with temporal constraints and version chain integrity.
    """

    def setUp(self):
        """Set up version testing environment."""
        super().setUp()
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123!'
        )
        self.auth = JWTAuthentication()
        self.token = self.auth.get_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        self.base_url = '/api/v1/versioned/'
        self.version_data = {
            'name': 'Test Resource',
            'content': 'Version 1',
            'effective_from': timezone.now().isoformat()
        }

    @freeze_time("2024-01-01")
    def test_version_chain_integrity(self):
        """Test version chain integrity and temporal constraints."""
        # Create initial version
        response = self.client.post(self.base_url, self.version_data)
        assert response.status_code == status.HTTP_201_CREATED
        initial_version = response.data
        
        # Create second version
        self.version_data['content'] = 'Version 2'
        self.version_data['effective_from'] = "2024-01-02T00:00:00Z"
        response = self.client.post(
            f"{self.base_url}{initial_version['id']}/versions/",
            self.version_data
        )
        assert response.status_code == status.HTTP_201_CREATED
        second_version = response.data
        
        # Verify version chain
        assert second_version['version'] == 2
        assert second_version['previous_version'] == initial_version['id']
        
        # Test temporal constraints
        invalid_data = self.version_data.copy()
        invalid_data['effective_from'] = "2024-01-01T00:00:00Z"
        response = self.client.post(
            f"{self.base_url}{second_version['id']}/versions/",
            invalid_data
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Test version retrieval
        response = self.client.get(
            f"{self.base_url}{initial_version['id']}/",
            {'version': 1}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['version'] == 1

@pytest.mark.django_db
class TestAuditViewSet(APITestCase):
    """
    Test cases for AuditViewSet with comprehensive change tracking.
    """

    def setUp(self):
        """Set up audit testing environment."""
        super().setUp()
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123!'
        )
        self.auth = JWTAuthentication()
        self.token = self.auth.get_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        self.base_url = '/api/v1/audited/'
        self.test_data = {
            'name': 'Test Resource',
            'description': 'Initial description',
            'metadata': {'key': 'value'}
        }

    def test_audit_logging(self):
        """Test comprehensive audit logging functionality."""
        # Test create with audit
        response = self.client.post(self.base_url, self.test_data)
        assert response.status_code == status.HTTP_201_CREATED
        resource_id = response.data['id']
        
        # Verify create audit log
        response = self.client.get(f"{self.base_url}{resource_id}/audit/")
        assert response.status_code == status.HTTP_200_OK
        audit_log = response.data['change_log']
        assert len(audit_log) == 1
        assert audit_log[0]['change_type'] == 'create'
        
        # Test update with audit
        update_data = {'description': 'Updated description'}
        response = self.client.patch(
            f"{self.base_url}{resource_id}/",
            update_data
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Verify update audit log
        response = self.client.get(f"{self.base_url}{resource_id}/audit/")
        assert response.status_code == status.HTTP_200_OK
        audit_log = response.data['change_log']
        assert len(audit_log) == 2
        assert audit_log[1]['change_type'] == 'update'
        assert audit_log[1]['changes']['description'] == 'Updated description'
        
        # Verify audit metadata
        assert 'user_id' in audit_log[1]
        assert 'timestamp' in audit_log[1]
        assert 'metadata' in audit_log[1]