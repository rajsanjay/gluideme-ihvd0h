"""
Comprehensive test suite for transfer requirement API views.
Validates CRUD operations, permissions, validation logic, response formats,
performance metrics, and data accuracy.

Version: 1.0
"""

# Django REST Framework v3.14+
from rest_framework.test import APITestCase
from rest_framework import status
from django.test import TestCase, override_settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.cache import cache

# Internal imports
from apps.requirements.models import TransferRequirement
from apps.requirements.views import TransferRequirementViewSet
from apps.institutions.models import Institution
from apps.courses.models import Course
from utils.exceptions import ValidationError

import time
from decimal import Decimal
from typing import Dict, List, Any
import json

User = get_user_model()

class TransferRequirementViewSetTests(APITestCase):
    """
    Comprehensive test suite for TransferRequirementViewSet covering CRUD operations,
    permissions, validation, performance, and accuracy.
    """
    maxDiff = None

    def setUp(self):
        """
        Set up test data with proper isolation and comprehensive fixtures.
        """
        # Clear cache
        cache.clear()

        # Create test institutions
        self.source_institution = Institution.objects.create(
            name="Test Community College",
            code="TCC",
            type="community_college",
            status="active",
            contact_info={
                "email": "contact@tcc.edu",
                "phone": "555-0100",
                "department": "Transfers"
            },
            address={
                "street": "123 College Ave",
                "city": "Test City",
                "state": "CA",
                "postal_code": "90210"
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
                "street": "456 University Dr",
                "city": "Test City",
                "state": "CA",
                "postal_code": "90211"
            }
        )

        # Create test users with different roles
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@test.com",
            password="testpass123"
        )

        self.institution_admin = User.objects.create_user(
            username="inst_admin",
            email="inst_admin@test.com",
            password="testpass123"
        )
        self.institution_admin.administered_institutions.add(self.source_institution)

        self.regular_user = User.objects.create_user(
            username="user",
            email="user@test.com",
            password="testpass123"
        )

        # Create test courses
        self.source_course = Course.objects.create(
            institution=self.source_institution,
            code="MATH 101",
            name="College Algebra",
            credits=Decimal("3.00"),
            status="active"
        )

        self.target_course = Course.objects.create(
            institution=self.target_institution,
            code="MATH 1A",
            name="Algebra I",
            credits=Decimal("3.00"),
            status="active"
        )

        # Create test requirement
        self.test_requirement = TransferRequirement.objects.create(
            source_institution=self.source_institution,
            target_institution=self.target_institution,
            major_code="CS",
            title="Computer Science Transfer",
            rules={
                "courses": ["MATH 101"],
                "min_credits": 3.0,
                "prerequisites": {}
            },
            metadata={
                "version_notes": "Initial version",
                "reviewer_id": str(self.admin_user.id),
                "approval_date": timezone.now().isoformat()
            },
            status="published"
        )

        # Set up API client
        self.client.force_authenticate(user=self.admin_user)
        self.api_url = "/api/v1/requirements/"

    def test_list_requirements(self):
        """Test requirement listing with filtering and pagination."""
        response = self.client.get(self.api_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 1)

        # Test filtering
        response = self.client.get(f"{self.api_url}?major_code=CS")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

        response = self.client.get(f"{self.api_url}?major_code=INVALID")
        self.assertEqual(len(response.data["results"]), 0)

    def test_create_requirement(self):
        """Test requirement creation with validation."""
        new_requirement = {
            "source_institution": str(self.source_institution.id),
            "target_institution": str(self.target_institution.id),
            "major_code": "MATH",
            "title": "Mathematics Transfer",
            "rules": {
                "courses": ["MATH 101"],
                "min_credits": 3.0,
                "prerequisites": {}
            },
            "metadata": {
                "version_notes": "Initial version",
                "reviewer_id": str(self.admin_user.id),
                "approval_date": timezone.now().isoformat()
            },
            "status": "draft"
        }

        response = self.client.post(
            self.api_url,
            data=json.dumps(new_requirement),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["major_code"], "MATH")

        # Test validation failure
        invalid_requirement = new_requirement.copy()
        invalid_requirement["rules"] = {}
        response = self.client.post(
            self.api_url,
            data=json.dumps(invalid_requirement),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_requirement(self):
        """Test requirement updates with version control."""
        update_data = {
            "rules": {
                "courses": ["MATH 101", "MATH 102"],
                "min_credits": 6.0,
                "prerequisites": {}
            },
            "metadata": {
                "version_notes": "Added MATH 102",
                "reviewer_id": str(self.admin_user.id),
                "approval_date": timezone.now().isoformat()
            }
        }

        response = self.client.patch(
            f"{self.api_url}{self.test_requirement.id}/",
            data=json.dumps(update_data),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["rules"]["courses"]), 2)
        self.assertEqual(response.data["version"], 2)

    @override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
    def test_response_time(self):
        """Validate API response times meet performance requirements."""
        # Test list endpoint
        start_time = time.time()
        response = self.client.get(self.api_url)
        list_time = time.time() - start_time
        self.assertLess(list_time, 0.5)  # 500ms requirement

        # Test create endpoint
        new_requirement = {
            "source_institution": str(self.source_institution.id),
            "target_institution": str(self.target_institution.id),
            "major_code": "BIO",
            "title": "Biology Transfer",
            "rules": {
                "courses": ["BIO 101"],
                "min_credits": 3.0,
                "prerequisites": {}
            },
            "metadata": {
                "version_notes": "Initial version",
                "reviewer_id": str(self.admin_user.id),
                "approval_date": timezone.now().isoformat()
            }
        }

        start_time = time.time()
        response = self.client.post(
            self.api_url,
            data=json.dumps(new_requirement),
            content_type="application/json"
        )
        create_time = time.time() - start_time
        self.assertLess(create_time, 0.5)

    def test_validation_accuracy(self):
        """Verify 99.99% accuracy in requirement validation."""
        # Create test dataset
        test_cases = self._generate_test_cases(1000)
        accurate_validations = 0

        for case in test_cases:
            try:
                response = self.client.post(
                    f"{self.api_url}{self.test_requirement.id}/validate_courses/",
                    data=json.dumps({"courses": case["courses"]}),
                    content_type="application/json"
                )
                
                if response.status_code == status.HTTP_200_OK:
                    if response.data["valid"] == case["expected_valid"]:
                        accurate_validations += 1
            except Exception as e:
                self.fail(f"Validation failed: {str(e)}")

        accuracy = (accurate_validations / len(test_cases)) * 100
        self.assertGreaterEqual(accuracy, 99.99)

    def test_permission_controls(self):
        """Test role-based access control."""
        # Test institution admin access
        self.client.force_authenticate(user=self.institution_admin)
        response = self.client.get(self.api_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test regular user access
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.post(self.api_url, data={})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def _generate_test_cases(self, count: int) -> List[Dict[str, Any]]:
        """Generate test cases for validation accuracy testing."""
        test_cases = []
        
        # Valid cases
        for i in range(count // 2):
            test_cases.append({
                "courses": ["MATH 101"],
                "expected_valid": True
            })
            
        # Invalid cases
        for i in range(count // 2):
            test_cases.append({
                "courses": ["INVALID 101"],
                "expected_valid": False
            })
            
        return test_cases