"""
ASGI config for Transfer Requirements Management System.

This module configures the ASGI application entry point for production deployment,
enabling high-performance asynchronous request handling and system availability.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

# v3.11+
import os

# v4.2+
from django.core.asgi import get_asgi_application

# Configure Django settings module for ASGI application
# This must be set before importing get_asgi_application()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

# Initialize ASGI application with production settings
# This creates an ASGI-compatible application object that:
# - Enables asynchronous request handling
# - Configures production-ready middleware
# - Sets up monitoring and logging
# - Initializes APM and tracing
application = get_asgi_application()

# The application object should be used with an ASGI server like:
# - Uvicorn (development): uvicorn config.asgi:application
# - Gunicorn (production): gunicorn config.asgi:application --worker-class uvicorn.workers.UvicornWorker