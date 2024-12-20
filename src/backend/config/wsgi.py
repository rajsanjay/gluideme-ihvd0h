"""
WSGI config for Transfer Requirements Management System.

This module exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/

Production deployment configuration:
- Server: Gunicorn v21.2+ 
- Worker Class: gevent
- Workers: 2-4 x num_cores
- Timeout: 30 seconds
- Max Requests: 1000
- Max Requests Jitter: 50
"""

# v3.11+
import os

# v4.2+
from django.core.wsgi import get_wsgi_application

# Configure Django's settings module for production environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

# Initialize WSGI application
application = get_wsgi_application()