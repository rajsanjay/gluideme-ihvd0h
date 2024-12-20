"""
Transfer Requirements Management System API
----------------------------------------
Package initializer for the REST API module that handles transfer requirement management.

This module provides version information and Django application configuration for the REST API.
It implements URI-based versioning and exposes the v1 API namespace.

Version: 1.0.0
Framework: Django REST Framework 3.14+
"""

from rest_framework import VERSION as DRF_VERSION
from distutils.version import StrictVersion

# API version number - used for version compatibility checking and documentation
__version__ = '1.0.0'

# Django application configuration path for automatic app registration
default_app_config = 'api.apps.ApiConfig'

# Import and expose v1 API namespace
from api.v1 import *  # noqa: F403

# Verify DRF version compatibility
MINIMUM_DRF_VERSION = '3.14.0'
if StrictVersion(DRF_VERSION) < StrictVersion(MINIMUM_DRF_VERSION):
    raise ImportError(
        f'Django REST Framework {MINIMUM_DRF_VERSION} or higher is required. '
        f'Found version {DRF_VERSION}'
    )

# Package metadata
__title__ = 'Transfer Requirements Management System API'
__author__ = 'TRMS Development Team'
__license__ = 'Proprietary'
__copyright__ = 'Copyright 2023 TRMS'

# Clean up namespace
del DRF_VERSION
del StrictVersion
del MINIMUM_DRF_VERSION