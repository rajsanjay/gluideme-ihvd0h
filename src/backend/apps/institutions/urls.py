"""
URL routing configuration for the institutions app.
Implements versioned API endpoints with caching and security controls.

Version: 1.0
"""

# Django imports v4.2+
from django.urls import path, include

# DRF imports v3.14+
from rest_framework.routers import DefaultRouter

# Django caching v4.2+
from django.views.decorators.cache import cache_page

# DRF throttling v3.14+
from rest_framework.decorators import throttle_classes

# Local imports
from apps.institutions.views import (
    InstitutionViewSet,
    InstitutionAgreementViewSet
)

# Initialize router with trailing slash configuration
router = DefaultRouter(trailing_slash=True)

# Register viewsets with versioned URLs
router.register(
    r'institutions',
    InstitutionViewSet,
    basename='institution'
)

router.register(
    r'institution-agreements',
    InstitutionAgreementViewSet,
    basename='institution-agreement'
)

# Define URL namespace
app_name = 'institutions'

# URL patterns with versioning, caching and security
urlpatterns = [
    # API v1 endpoints
    path('api/v1/', include([
        # Core router URLs with rate limiting
        path('', include((router.urls, 'v1'), namespace='v1')),

        # Custom institution endpoints with caching
        path(
            'institutions/<uuid:pk>/active-courses/',
            cache_page(1800)(  # 30 minute cache
                InstitutionViewSet.as_view({'get': 'active_courses'})
            ),
            name='institution-active-courses'
        ),
        
        path(
            'institutions/<uuid:pk>/transfer-requirements/',
            cache_page(1800)(  # 30 minute cache
                InstitutionViewSet.as_view({'get': 'get_transfer_requirements'})
            ),
            name='institution-transfer-requirements'
        ),

        # Institution agreement validation endpoint
        path(
            'institution-agreements/<uuid:pk>/check-active/',
            InstitutionAgreementViewSet.as_view({'get': 'validate_dates'}),
            name='agreement-validate-dates'
        ),
    ])),
]