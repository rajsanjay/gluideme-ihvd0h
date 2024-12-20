"""
Core URL routing configuration for the Transfer Requirements Management System.
Implements versioned API endpoints, audit logging, and role-based access control.

Version: 1.0
"""

# Django v4.2+
from django.urls import path, include

# Django REST Framework v3.14+
from rest_framework.routers import DefaultRouter
from rest_framework.urlpatterns import format_suffix_patterns

# Internal imports
from apps.core.views import (
    BaseViewSet,
    VersionedViewSet,
    AuditViewSet
)

# Initialize router with trailing slash for consistency
router = DefaultRouter(trailing_slash=True)

def register_core_routes(router):
    """
    Register core viewsets with enhanced security and monitoring.
    
    Args:
        router: DefaultRouter instance
        
    Note:
        Implements role-based access control and audit logging for all routes.
    """
    # Base routes with security middleware
    router.register(
        r'base',
        BaseViewSet,
        basename='core-base'
    )

    # Version control routes with rollback support
    router.register(
        r'versions',
        VersionedViewSet,
        basename='core-versions'
    )

    # Audit log routes with enhanced security
    router.register(
        r'audit-logs',
        AuditViewSet,
        basename='core-audit'
    )

# Register core routes
register_core_routes(router)

# Define URL patterns with versioning and security
app_name = 'core'
urlpatterns = [
    # API version 1 routes
    path('api/v1/', include([
        # Core viewset routes
        path('', include(router.urls)),
        
        # Version management endpoints
        path('versions/<uuid:pk>/history/', 
             VersionedViewSet.as_view({'get': 'get_version_history'}),
             name='version-history'),
        path('versions/<uuid:pk>/rollback/',
             VersionedViewSet.as_view({'post': 'rollback_version'}),
             name='version-rollback'),
        
        # Audit log endpoints with role-based access
        path('audit-logs/search/',
             AuditViewSet.as_view({'get': 'search'}),
             name='audit-search'),
        path('audit-logs/export/',
             AuditViewSet.as_view({'get': 'export'}),
             name='audit-export'),
        
        # Health check endpoint
        path('health/',
             BaseViewSet.as_view({'get': 'health_check'}),
             name='health-check'),
    ])),
]

# Add format suffix patterns for content negotiation
urlpatterns = format_suffix_patterns(urlpatterns, allowed=['json', 'api'])