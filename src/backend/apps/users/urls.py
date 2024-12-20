"""
URL routing configuration for user management endpoints in the Transfer Requirements Management System.
Implements secure, versioned, and monitored API endpoints with rate limiting.

Version: 1.0
"""

# Django URL routing v4.2+
from django.urls import path, include

# Django REST Framework v3.14+
from rest_framework.routers import DefaultRouter

# User management views
from apps.users.views import (
    UserViewSet,
    UserRegistrationView,
    PasswordChangeView,
    HealthCheckView,
    MetricsView
)

# Initialize router with trailing slash for consistency
router = DefaultRouter(trailing_slash=True)

# Register user management viewset with versioning
router.register(
    r'users',
    UserViewSet,
    basename='user'
)

# Application namespace for URL reversing
app_name = 'users'

# URL patterns with versioning and rate limiting
urlpatterns = [
    # API version 1 endpoints
    path('api/v1/', include([
        # User registration with rate limiting
        path(
            'register/',
            UserRegistrationView.as_view(),
            name='user-registration'
        ),
        
        # Password management with rate limiting
        path(
            'change-password/',
            PasswordChangeView.as_view(),
            name='password-change'
        ),
        
        # ViewSet URLs for user management
        path(
            '',
            include(router.urls)
        ),
        
        # Health check endpoint for monitoring
        path(
            'health/',
            HealthCheckView.as_view(),
            name='health-check'
        ),
        
        # Metrics endpoint for monitoring
        path(
            'metrics/',
            MetricsView.as_view(),
            name='metrics'
        )
    ])),
]

# Export URL patterns for Django URL resolver
__all__ = ['urlpatterns']