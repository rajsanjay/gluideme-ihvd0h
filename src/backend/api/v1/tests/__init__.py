"""
Test package initialization for API v1 tests providing comprehensive test environment
configuration, common test utilities, validation accuracy tracking, and enhanced error
handling coverage for API endpoint testing.

Version: 1.0
"""

from rest_framework.test import APITestCase  # v3.14+
from rest_framework import status  # v3.14+
from django.test import override_settings  # v4.2+
from api.v1.views import TransferRequirementViewSet
from api.v1.serializers import TransferRequirementSerializer
from apps.institutions.models import Institution
from apps.courses.models import Course
from apps.requirements.models import TransferRequirement
from utils.exceptions import ValidationError
from django.utils import timezone
import time
from typing import Dict, Any, List, Optional
import logging

# Configure test logger
logger = logging.getLogger(__name__)

# Test configuration constants
TEST_PASSWORD = 'testpass123'
TEST_USER_EMAIL = 'test@example.com'
VALIDATION_ACCURACY_THRESHOLD = 0.9999  # 99.99% accuracy requirement
PERFORMANCE_THRESHOLD_MS = 500  # 500ms max response time

@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'
        }
    }
)
class APIv1TestCase(APITestCase):
    """
    Enhanced base test case class for API v1 tests providing common utilities,
    setup, validation accuracy tracking, and performance monitoring.
    """
    base_url = '/api/v1/'
    maxDiff = None
    validation_accuracy = 0.0
    performance_metrics = {}

    def setUp(self) -> None:
        """
        Enhanced test environment setup with validation tracking.
        Configures test client, authentication, and initializes metrics.
        """
        super().setUp()

        # Configure test client with CSRF checks
        self.client.enforce_csrf_checks = True

        # Create test user with required permissions
        self.user = self.create_test_user()
        self.client.force_authenticate(user=self.user)

        # Initialize validation tracking
        self.validation_count = 0
        self.successful_validations = 0
        self.validation_errors = []

        # Initialize performance monitoring
        self.performance_metrics = {
            'total_time': 0,
            'request_count': 0,
            'slow_requests': [],
            'average_response_time': 0
        }

        # Clear test cache
        from django.core.cache import cache
        cache.clear()

    def tearDown(self) -> None:
        """
        Clean up test environment and record metrics.
        """
        # Record final validation accuracy
        if self.validation_count > 0:
            self.validation_accuracy = (
                self.successful_validations / self.validation_count
            )

        # Log test metrics
        logger.info(
            "Test metrics",
            extra={
                'validation_accuracy': self.validation_accuracy,
                'performance_metrics': self.performance_metrics,
                'validation_errors': self.validation_errors
            }
        )

        super().tearDown()

    def create_test_user(self) -> Any:
        """Create test user with required permissions."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        user = User.objects.create_user(
            email=TEST_USER_EMAIL,
            password=TEST_PASSWORD
        )
        
        # Add required permissions
        from django.contrib.auth.models import Permission
        permissions = Permission.objects.filter(
            codename__in=['add_transferrequirement', 'change_transferrequirement']
        )
        user.user_permissions.add(*permissions)
        
        return user

    def create_test_data(self, additional_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create comprehensive test data with validation.
        
        Args:
            additional_data: Optional additional test data
            
        Returns:
            Dict: Dictionary of created test objects
        """
        # Create test institutions
        source_institution = Institution.objects.create(
            name="Test Source Institution",
            code="TSI",
            type="university",
            status="active"
        )
        
        target_institution = Institution.objects.create(
            name="Test Target Institution",
            code="TTI",
            type="university",
            status="active"
        )

        # Create test courses
        course1 = Course.objects.create(
            institution=source_institution,
            code="CS 101",
            name="Introduction to Programming",
            credits="3.00",
            status="active"
        )
        
        course2 = Course.objects.create(
            institution=source_institution,
            code="CS 102",
            name="Data Structures",
            credits="3.00",
            status="active",
            prerequisites=[course1]
        )

        # Create test requirement
        requirement = TransferRequirement.objects.create(
            source_institution=source_institution,
            target_institution=target_institution,
            major_code="CS",
            title="Computer Science Transfer Requirements",
            type="major",
            rules={
                'courses': [course1.code, course2.code],
                'min_credits': 6,
                'prerequisites': {
                    'CS 102': ['CS 101']
                }
            },
            status="published"
        )

        test_data = {
            'source_institution': source_institution,
            'target_institution': target_institution,
            'courses': [course1, course2],
            'requirement': requirement
        }

        if additional_data:
            test_data.update(additional_data)

        return test_data

    def track_validation_accuracy(self, validation_result: bool) -> float:
        """
        Track validation accuracy for test cases.
        
        Args:
            validation_result: Result of validation check
            
        Returns:
            float: Current validation accuracy
        """
        self.validation_count += 1
        if validation_result:
            self.successful_validations += 1
        else:
            self.validation_errors.append({
                'timestamp': timezone.now().isoformat(),
                'test_name': self._testMethodName
            })

        current_accuracy = (
            self.successful_validations / self.validation_count
            if self.validation_count > 0 else 0.0
        )

        # Log if accuracy drops below threshold
        if current_accuracy < VALIDATION_ACCURACY_THRESHOLD:
            logger.warning(
                f"Validation accuracy below threshold: {current_accuracy}",
                extra={
                    'threshold': VALIDATION_ACCURACY_THRESHOLD,
                    'validation_errors': self.validation_errors
                }
            )

        return current_accuracy

    def measure_performance(self, test_function: callable) -> Dict[str, Any]:
        """
        Measure and track API performance metrics.
        
        Args:
            test_function: Function to measure
            
        Returns:
            Dict: Performance metrics
        """
        start_time = time.time()
        result = test_function()
        execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        # Update metrics
        self.performance_metrics['total_time'] += execution_time
        self.performance_metrics['request_count'] += 1
        self.performance_metrics['average_response_time'] = (
            self.performance_metrics['total_time'] / 
            self.performance_metrics['request_count']
        )

        # Track slow requests
        if execution_time > PERFORMANCE_THRESHOLD_MS:
            self.performance_metrics['slow_requests'].append({
                'test_name': self._testMethodName,
                'execution_time': execution_time,
                'timestamp': timezone.now().isoformat()
            })
            logger.warning(
                f"Slow request detected: {execution_time}ms",
                extra={
                    'threshold': PERFORMANCE_THRESHOLD_MS,
                    'test_name': self._testMethodName
                }
            )

        return {
            'execution_time': execution_time,
            'result': result
        }