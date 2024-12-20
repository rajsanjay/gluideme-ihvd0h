#!/usr/bin/env python
"""
Django's command-line utility for administrative tasks with enhanced error handling
and environment validation for the Transfer Requirements Management System.

This script serves as the main entry point for executing Django management commands
and includes additional features for:
- Environment validation and configuration
- Comprehensive error handling and logging
- Command execution tracking
- Status code management
"""

import os  # v3.11+
import sys  # v3.11+
import logging  # v3.11+
from django.core.exceptions import ImproperlyConfigured  # v4.2+
from django.conf import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """
    Enhanced main function that runs Django's administrative tasks with improved
    error handling and environment validation.
    
    Returns:
        int: Exit status code
            0: Success
            1: Configuration error
            2: Execution error
    """
    try:
        # Set default Django settings module if not already set
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
        settings_module = os.environ['DJANGO_SETTINGS_MODULE']
        
        # Validate settings module path
        if not any(settings_module.endswith(env) for env in ['development', 'production', 'staging', 'test']):
            raise ImproperlyConfigured(
                f"Invalid settings module: {settings_module}. Must be one of: "
                "config.settings.[development|production|staging|test]"
            )
        
        logger.info(f"Using settings module: {settings_module}")
        
        try:
            from django.core.management import execute_from_command_line
        except ImportError as exc:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            ) from exc
            
        # Initialize Django
        try:
            import django
            django.setup()
        except Exception as exc:
            logger.error(f"Failed to initialize Django: {str(exc)}")
            return 1
            
        # Log command execution
        command = ' '.join(sys.argv)
        logger.info(f"Executing command: {command}")
        
        # Execute management command
        execute_from_command_line(sys.argv)
        
        return 0
        
    except ImproperlyConfigured as exc:
        logger.error(f"Configuration error: {str(exc)}")
        return 1
    except Exception as exc:
        logger.error(f"Command execution failed: {str(exc)}")
        return 2

if __name__ == '__main__':
    sys.exit(main())