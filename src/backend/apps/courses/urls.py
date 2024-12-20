"""
URL routing configuration for the courses Django app.
Implements versioned API endpoints with performance optimization, rate limiting, and OpenAPI documentation.

Version: 1.0
"""

# Django imports - v4.2+
from django.urls import path, include

# Django REST Framework imports - v3.14+
from rest_framework.routers import DefaultRouter
from rest_framework.decorators import throttle_classes

# Django cache imports - v4.2+
from django.views.decorators.cache import cache_page

# Third-party imports
from drf_spectacular.views import get_schema_view  # v0.26+

# Local imports
from apps.courses.views import (
    CourseViewSet,
    CourseEquivalencyViewSet
)

# Configure app name for URL namespacing
app_name = 'courses'

# Initialize DRF router with trailing slash configuration
router = DefaultRouter(trailing_slash=True)

# Register viewsets with optimized URL patterns
router.register(
    r'courses',
    CourseViewSet,
    basename='course'
)
router.register(
    r'course-equivalencies',
    CourseEquivalencyViewSet,
    basename='course-equivalency'
)

# Configure OpenAPI schema view
schema_view = get_schema_view(
    title='Courses API',
    description='API endpoints for course and equivalency management',
    version='1.0.0',
    patterns=[path('api/v1/', include(router.urls))]
)

# Custom rate limit class for health check
class HealthCheckRateThrottle:
    """Rate limiting for health check endpoint."""
    rate = '60/minute'
    scope = 'health_check'

@cache_page(60)  # Cache for 1 minute
@throttle_classes([HealthCheckRateThrottle])
def health_check(request):
    """
    API health check endpoint with rate limiting and caching.
    
    Returns:
        dict: Health status response
    """
    return {
        'status': 'healthy',
        'version': '1.0.0',
        'timestamp': timezone.now().isoformat()
    }

# Define URL patterns with versioning and documentation
urlpatterns = [
    # API v1 endpoints
    path(
        'api/v1/',
        include([
            # Course management endpoints
            path('', include(router.urls)),
            
            # OpenAPI schema and documentation
            path(
                'schema/',
                schema_view.with_ui('swagger', cache_timeout=3600),
                name='schema'
            ),
            
            # Health check endpoint
            path(
                'health/',
                health_check,
                name='health'
            ),
        ])
    ),
]