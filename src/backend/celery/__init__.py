"""
Celery Initialization Module
Version: Celery 5.3+
Purpose: Initializes and exports the main Celery application instance with configuration validation
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from celery import Celery

# Import the configured Celery application instance
from .app import app

# Version information
__version__ = '1.0.0'

# Define exported symbols
__all__ = ['app']

def _validate_config(app: 'Celery') -> None:
    """
    Validates the Celery application configuration before export.
    
    Args:
        app: Configured Celery application instance
        
    Raises:
        ValueError: If any configuration validation fails
    """
    # Validate broker URL configuration
    if not app.conf.broker_url:
        raise ValueError("Celery broker URL must be configured")
    
    # Validate result backend configuration
    if not app.conf.result_backend:
        raise ValueError("Celery result backend must be configured")
    
    # Validate task serializer settings
    if app.conf.task_serializer != 'json' or 'json' not in app.conf.accept_content:
        raise ValueError("Task serializer must be configured for JSON")
    
    # Validate worker concurrency settings
    if not app.conf.worker_prefetch_multiplier == 1:
        raise ValueError("Worker prefetch multiplier must be set to 1 for fair task distribution")
    
    # Validate queue configurations
    required_queues = {'requirements', 'validation', 'search', 'notifications'}
    configured_queues = set(app.conf.task_queues.keys()) if app.conf.task_queues else set()
    
    if not required_queues.issubset(configured_queues):
        raise ValueError(f"Missing required queue configurations: {required_queues - configured_queues}")

# Validate the application configuration
_validate_config(app)

# The app instance is already configured in app.py, so we just need to re-export it
# This allows other modules to import the Celery instance directly from celery.__init__