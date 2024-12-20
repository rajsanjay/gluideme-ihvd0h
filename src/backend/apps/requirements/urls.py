"""
URL routing configuration for the requirements app.
Implements versioned API endpoints for transfer requirement management with security integration.

Version: 1.0
"""

# Django v4.2+
from django.urls import path, include

# Django REST Framework v3.14+
from rest_framework.routers import DefaultRouter

# Internal imports
from apps.requirements.views import (
    TransferRequirementViewSet,
    RequirementHealthCheck
)

# Configure DRF router with versioning support
router = DefaultRouter(trailing_slash=True)
router.register(
    r'requirements',
    TransferRequirementViewSet,
    basename='requirement'
)

# Define app namespace for URL isolation
app_name = 'requirements'

# URL patterns with versioned API endpoints
urlpatterns = [
    # API v1 endpoints
    path('api/v1/', include([
        # Router-generated requirement endpoints:
        # - GET/POST /api/v1/requirements/
        # - GET/PUT/PATCH/DELETE /api/v1/requirements/{id}/
        path('', include(router.urls)),

        # Custom requirement actions
        path(
            'requirements/<uuid:pk>/validate/',
            TransferRequirementViewSet.as_view({'post': 'validate_courses'}),
            name='requirement-validate'
        ),
        path(
            'requirements/<uuid:pk>/versions/',
            TransferRequirementViewSet.as_view({'get': 'list_versions'}),
            name='requirement-versions'
        ),

        # Health check endpoint
        path(
            'requirements/health/',
            RequirementHealthCheck.as_view(),
            name='requirement-health'
        ),
    ])),
]

# Export URL patterns for Django URL resolver
__all__ = ['urlpatterns']