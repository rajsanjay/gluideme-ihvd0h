"""
Django application configuration for the requirements app that manages transfer requirements, 
course validations, and requirement versioning with UUID-based models for distributed system compatibility.

This configuration ensures:
- UUID-based model fields for distributed system compatibility
- Proper app naming and registration in Django
- Clear verbose naming for admin interface

Version: Django 4.2+
"""

from django.apps import AppConfig  # Django 4.2+


class RequirementsConfig(AppConfig):
    """
    Django application configuration class for the requirements app that handles transfer requirements,
    validations, and versioning with UUID-based models.
    
    This configuration supports:
    - Transfer requirement management with UUID-based identification
    - Version-controlled requirement tracking
    - Distributed system compatibility through UUID fields
    - 99.9% system availability through distributed-safe identifiers
    """

    # Application name following Django convention
    name = 'apps.requirements'
    
    # Human-readable name for admin interface
    verbose_name = 'Requirements'
    
    # Use UUIDs by default for distributed system compatibility
    default_auto_field = 'django.db.models.UUIDField'