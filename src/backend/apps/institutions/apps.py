"""
Django application configuration for the institutions app that manages educational institution data
and relationships within the transfer requirements management system.

This configuration sets up proper app namespace, secure UUID-based identification, and supports
data classification levels for institution data handling.

Version: Django 4.2+
"""

from django.apps import AppConfig  # Django 4.2+


class InstitutionsConfig(AppConfig):
    """
    Django application configuration for the institutions app.
    
    Manages educational institution data with secure UUID-based identification and proper
    app namespace configuration. Supports data classification levels (Highly Sensitive,
    Sensitive, Public, Internal) through model configuration.
    
    Attributes:
        name (str): Dotted path name for the app following project namespace structure
        verbose_name (str): Human-readable app name for admin interface
        default_auto_field (str): UUID field for secure primary key generation
    """
    
    # App namespace configuration following project structure
    name = 'apps.institutions'
    
    # Human-readable name for admin interface
    verbose_name = 'Institutions'
    
    # Use UUID for secure primary key generation
    default_auto_field = 'django.db.models.UUIDField'