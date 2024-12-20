"""
URL routing configuration for API v1 endpoints of the Transfer Requirements Management System.
Implements RESTful URL patterns with versioning, custom validation routes, and optimized URL resolution.

Version: 1.0
"""

from django.urls import path, include  # v4.2+
from rest_framework.routers import DefaultRouter  # v3.14+
from api.v1.views import (
    TransferRequirementViewSet,
    CourseViewSet
)

# Configure DRF router with optimized settings
router = DefaultRouter(
    trailing_slash=True,
    schema_title='Transfer Requirements API v1'
)

# Register viewsets with explicit base names for clarity
router.register(
    r'requirements',
    TransferRequirementViewSet,
    basename='requirement'
)
router.register(
    r'courses',
    CourseViewSet,
    basename='course'
)

# Define app namespace for versioning support
app_name = 'api_v1'

# URL patterns with optimized ordering and custom endpoints
urlpatterns = [
    # Include router URLs with namespace
    path('', include(router.urls)),

    # Custom validation endpoints for requirements
    path(
        'requirements/<uuid:pk>/validate-courses/',
        TransferRequirementViewSet.as_view({'post': 'validate_courses'}),
        name='requirement-validate-courses'
    ),

    # Custom validation endpoints for courses
    path(
        'courses/<uuid:pk>/check-transfer/',
        CourseViewSet.as_view({'post': 'check_transfer_validity'}),
        name='course-check-transfer'
    ),
]