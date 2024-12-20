"""
Production settings for Transfer Requirements Management System.
Extends base settings with production-specific configurations for security, performance and monitoring.
"""

# v3.11+
import os

# v1.28+
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

# v3.0+
import watchtower

# v1.20+
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.sampling import ParentBasedTraceIdRatioBased
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# v0.17+
from prometheus_client import CollectorRegistry, multiprocess

# Import all from base settings
from .base import *

# Debug must be False in production
DEBUG = False

# Allowed hosts should be set from environment variable
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Static and media files configuration
STATIC_ROOT = '/var/www/static/'
MEDIA_ROOT = '/var/www/media/'
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# AWS S3 custom domain for static/media files
AWS_S3_CUSTOM_DOMAIN = f"{os.getenv('AWS_STORAGE_BUCKET_NAME')}.s3.amazonaws.com"

# CORS configuration
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')
CORS_ALLOW_CREDENTIALS = True

# Enhanced logging configuration for production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s %(trace_id)s %(span_id)s'
        }
    },
    'filters': {
        'trace_context': {
            '()': 'apps.core.logging.TraceContextFilter'
        }
    },
    'handlers': {
        'cloudwatch': {
            'class': 'watchtower.CloudWatchLogHandler',
            'log_group': 'django-production',
            'log_stream_name': 'application-{strftime:%Y-%m-%d}',
            'formatter': 'json',
            'filters': ['trace_context'],
            'use_queues': True,
            'batch_size': 100,
            'create_log_group': True
        },
        'prometheus': {
            'class': 'apps.core.logging.PrometheusLogHandler',
            'formatter': 'json'
        }
    },
    'loggers': {
        'django': {
            'handlers': ['cloudwatch', 'prometheus'],
            'level': 'INFO',
            'propagate': True,
        },
        'apps': {
            'handlers': ['cloudwatch', 'prometheus'],
            'level': 'INFO',
            'propagate': True,
        }
    }
}

# Production cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'RETRY_ON_TIMEOUT': True,
            'MAX_CONNECTIONS': 1000,
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 100
            }
        }
    }
}

# OpenTelemetry configuration for distributed tracing
OPENTELEMETRY_CONFIG = {
    'TRACER_NAME': 'transfer-requirements-api',
    'SAMPLER': 'opentelemetry.sdk.trace.sampling.ParentBasedTracing',
    'SAMPLER_ARGS': {
        'root': 'opentelemetry.sdk.trace.sampling.TraceIdRatioBased',
        'root_args': [0.1]  # Sample 10% of requests
    },
    'EXPORTER': 'opentelemetry.exporter.otlp.proto.grpc.trace_exporter.OTLPSpanExporter',
    'EXPORTER_ARGS': {
        'endpoint': os.getenv('OTLP_ENDPOINT'),
        'insecure': False
    }
}

# Initialize OpenTelemetry tracer
tracer_provider = TracerProvider(
    sampler=ParentBasedTraceIdRatioBased(TraceIdRatioBased(0.1))
)
trace.set_tracer_provider(tracer_provider)
tracer_provider.add_span_processor(
    BatchSpanProcessor(
        OTLPSpanExporter(
            endpoint=OPENTELEMETRY_CONFIG['EXPORTER_ARGS']['endpoint'],
            insecure=OPENTELEMETRY_CONFIG['EXPORTER_ARGS']['insecure']
        )
    )
)

# Prometheus metrics configuration
PROMETHEUS_METRICS = {
    'ENABLED': True,
    'ENDPOINT': '/metrics',
    'LABELS': {
        'application': 'transfer-requirements-api',
        'environment': 'production'
    }
}

# Initialize multiprocess prometheus metrics for gunicorn workers
if 'prometheus_multiproc_dir' in os.environ:
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)

# Additional security headers
MIDDLEWARE += [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'csp.middleware.CSPMiddleware',
]

# Content Security Policy settings
CSP_DEFAULT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_SCRIPT_SRC = ("'self'",)
CSP_IMG_SRC = ("'self'", "data:", "*.amazonaws.com")
CSP_FONT_SRC = ("'self'", "data:")
CSP_CONNECT_SRC = ("'self'", "*.amazonaws.com")

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_NAME = '__Host-sessionid'
SESSION_COOKIE_SAMESITE = 'Lax'

# Email configuration for production
EMAIL_BACKEND = 'django_ses.SESBackend'
AWS_SES_REGION_NAME = os.getenv('AWS_SES_REGION_NAME', 'us-west-2')
AWS_SES_CONFIGURATION_SET = 'transfer-requirements'

# File upload configuration
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_PERMISSIONS = 0o644