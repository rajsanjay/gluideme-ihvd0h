"""
Main URL configuration for the Transfer Requirements Management System.
Implements versioned API routing, authentication endpoints, security middleware,
rate limiting, and monitoring endpoints.

Version: 1.0
"""

# Django v4.2+
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

# Django REST Framework v3.14+
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView
)

# Health check and monitoring v3.17+
from health_check.views import HealthCheckView
from django_prometheus.views import MetricsView

# Internal imports
from api.v1.urls import urlpatterns as api_v1_urls
from apps.core.urls import urlpatterns as core_urls
from apps.users.urls import urlpatterns as users_urls

# Define root URL patterns with versioning and security
urlpatterns = [
    # API version 1 endpoints with rate limiting
    path('api/v1/', include([
        # Core API routes
        path('', include(api_v1_urls)),
        
        # Authentication endpoints
        path('auth/token/', 
            TokenObtainPairView.as_view(),
            name='token-obtain'
        ),
        path('auth/token/refresh/',
            TokenRefreshView.as_view(),
            name='token-refresh'
        ),
        
        # User management routes
        path('users/', include(users_urls)),
        
        # Core functionality routes
        path('core/', include(core_urls)),
        
        # Health check endpoint
        path('health/',
            HealthCheckView.as_view(
                checks=['db', 'cache', 'storage']
            ),
            name='health-check'
        ),
        
        # Metrics endpoint (admin only)
        path('metrics/',
            MetricsView.as_view(),
            name='metrics'
        ),
    ])),
]

# Add static/media file serving in development
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )

# Add security headers middleware
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = not settings.DEBUG
SESSION_COOKIE_SECURE = not settings.DEBUG
CSRF_COOKIE_SECURE = not settings.DEBUG

# Configure rate limiting
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',  # Anonymous users
        'user': '1000/hour'  # Authenticated users
    }
}

# Configure monitoring
PROMETHEUS_METRICS = True
PROMETHEUS_EXPORT_MIGRATIONS = False

# Handler for production error pages
handler404 = 'apps.core.views.custom_404'
handler500 = 'apps.core.views.custom_500'