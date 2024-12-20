"""
Python package initializer for the institutions Django app.

This module enables automatic Django app registration and configuration for the institutions app
which manages educational institution data and relationships within the transfer requirements
management system. It provides secure UUID-based identification and supports data classification
levels for institution data handling.

Version: Django 4.2+
"""

# Specify the default app configuration for Django's app registry
# This enables automatic app registration and proper initialization
default_app_config = 'apps.institutions.apps.InstitutionsConfig'