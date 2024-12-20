"""
Core Django application initialization module that configures foundational functionality
for the transfer requirements management system.

This module sets up:
- Default app configuration for Django app registry
- UUID-based field configuration
- Core app discovery and initialization

Version: Django 4.2+
"""

# Import core app configuration that defines essential Django app settings
from apps.core.apps import CoreConfig

# Configure the default Django app configuration to enable proper app registration
default_app_config = 'apps.core.apps.CoreConfig'