"""
Main entry point and task registry for Celery tasks in the Transfer Requirements Management System.
Provides centralized task imports and exports with comprehensive error handling, monitoring,
and queue management for asynchronous processing.

Version: 1.0.0
Author: Transfer Requirements Management System Team
"""

# Re-export task functions for notifications, requirements, search, and validation
from celery.tasks.notifications import send_requirement_update_notification
from celery.tasks.requirements import process_requirement_validation
from celery.tasks.search import update_search_indexes
from celery.tasks.validation import process_validation_rule

# Version and metadata
__version__ = "1.0.0"
__author__ = "Transfer Requirements Management System Team"

# Define public interface
__all__ = [
    "send_requirement_update_notification",
    "process_requirement_validation",
    "update_search_indexes",
    "process_validation_rule"
]

# Task queue configuration is handled in celery/config.py
# Task routing and worker settings are managed in celery/app.py