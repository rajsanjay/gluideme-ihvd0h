"""
Celery Application Configuration
Version: Celery 5.3+
Purpose: Main Celery application configuration for the Transfer Requirements Management System
"""

import os
from celery import Celery
from celery.config import get_queue_config, get_task_routes

# Initialize Celery application with core settings
app = Celery(
    'transfer_requirements',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0'),
    timezone='UTC',
    task_serializer='json',
    result_serializer='json',
    accept_content=['json']
)

def configure_celery():
    """
    Configures the Celery application with enterprise-grade settings including:
    - Optimized queue configurations with priority levels
    - Dead Letter Exchange (DLX) for failed tasks
    - Worker performance tuning
    - Memory management
    - Task routing and retry policies
    
    Returns:
        Celery: Configured Celery application instance
    """
    # Load comprehensive queue configuration
    queue_config = get_queue_config()
    app.conf.update(queue_config)
    
    # Configure task routing with priority queues
    app.conf.task_routes = get_task_routes()
    
    # Worker optimization settings
    app.conf.worker_prefetch_multiplier = 1  # Prevent worker starvation
    app.conf.worker_max_tasks_per_child = 1000  # Memory leak prevention
    app.conf.worker_max_memory_per_child = 400000  # 400MB memory limit
    
    # Task execution limits
    app.conf.task_time_limit = 3600  # Hard limit: 1 hour
    app.conf.task_soft_time_limit = 3300  # Soft limit: 55 minutes
    
    # Enable task events for monitoring
    app.conf.worker_send_task_events = True
    app.conf.task_send_sent_event = True
    
    # Result backend optimization
    app.conf.result_expires = 86400  # Results expire after 24 hours
    app.conf.result_persistent = True  # Persist results in backend
    
    # Task acknowledgment and retry settings
    app.conf.task_acks_late = True  # Acknowledge after task completion
    app.conf.task_reject_on_worker_lost = True  # Requeue tasks on worker failure
    app.conf.task_default_retry_delay = 180  # 3 minutes retry delay
    app.conf.task_max_retries = 3  # Maximum retry attempts
    
    # Security settings
    app.conf.task_serializer = 'json'
    app.conf.result_serializer = 'json'
    app.conf.accept_content = ['json']
    
    return app

# Configure and initialize the Celery application
app = configure_celery()

# Optional: Configure logging
app.log.setup_logging_subsystem()

# Make the Celery app importable
__all__ = ['app']