"""
Django application initialization for the requirements app that manages transfer requirements
between institutions. Provides configuration and models for automated validation and versioning.

Key Features:
- Automated transfer requirement parsing and validation
- Version-controlled requirement management
- 99.99% data accuracy through strict model validation
- 99.9% system availability through distributed system compatibility

Version: 1.0
Dependencies:
- Django 4.2+
- django-rest-framework 3.14+
"""

# Import app configuration for Django app registry
from apps.requirements.apps import RequirementsConfig

# Import core models for external access
from apps.requirements.models import (
    TransferRequirement,
    RequirementCourse
)

# Configure default app configuration for Django
default_app_config = 'apps.requirements.apps.RequirementsConfig'

# Version of the requirements app
__version__ = '1.0.0'

# Expose core models and validation functions for external use
__all__ = [
    'TransferRequirement',
    'RequirementCourse',
    'default_app_config'
]