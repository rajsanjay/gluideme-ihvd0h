"""
URL routing configuration for the validation app.
Defines endpoints for course validation operations, validation records management, and cache control.

Version: 1.0
"""

# django.urls v4.2+
from django.urls import path, include
# rest_framework.routers v3.14+
from rest_framework.routers import DefaultRouter
from apps.validation.views import ValidationRecordViewSet, ValidationCacheViewSet

# Initialize router with trailing slash for consistency
router = DefaultRouter(trailing_slash=True)

# Register viewsets with descriptive base names
router.register(
    r'records',
    ValidationRecordViewSet,
    basename='validation-record'
)

# Define URL patterns with versioning
app_name = 'validation'
urlpatterns = [
    # API version 1 endpoints
    path('api/v1/', include([
        # Single course validation endpoint
        path(
            'validate/',
            ValidationRecordViewSet.as_view({'post': 'validate_course'}),
            name='validate-course'
        ),
        
        # Bulk validation endpoint
        path(
            'validate/bulk/',
            ValidationRecordViewSet.as_view({'post': 'bulk_validate_courses'}),
            name='bulk-validate'
        ),
        
        # Validation records management endpoints
        path(
            'records/',
            ValidationRecordViewSet.as_view({'get': 'list', 'post': 'create'}),
            name='validation-records'
        ),
        path(
            'records/<uuid:pk>/',
            ValidationRecordViewSet.as_view({
                'get': 'retrieve',
                'put': 'update',
                'patch': 'partial_update',
                'delete': 'destroy'
            }),
            name='validation-record-detail'
        ),
        
        # Cache management endpoints
        path(
            'cache/',
            ValidationCacheViewSet.as_view({'get': 'list'}),
            name='cache-list'
        ),
        path(
            'cache/clear/',
            ValidationCacheViewSet.as_view({'post': 'clear_cache'}),
            name='clear-cache'
        ),
        path(
            'cache/refresh/',
            ValidationCacheViewSet.as_view({'post': 'refresh_cache'}),
            name='refresh-cache'
        ),
    ])),
    
    # Include router URLs for additional endpoints
    path('', include(router.urls)),
]