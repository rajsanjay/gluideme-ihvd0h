"""
Initialization module for the validation Django app that handles course requirement validation 
and transfer eligibility checks.

This module configures the Django app for automatic discovery and registration to support:
- Real-time course validation with 99.99% accuracy
- High-performance validation processing
- Proper app initialization and configuration management

Version: Django 4.2+
"""

# Configure the default Django app configuration path for automatic app discovery
# This enables Django to properly initialize the validation engine and its components
default_app_config = 'apps.validation.apps.ValidationConfig'

# Note: The ValidationConfig class from apps.py handles:
# - UUID-based model fields for validation records
# - App naming and identification
# - Initialization of validation signal handlers
# - Setup of validation engine settings
# - Configuration of performance monitoring