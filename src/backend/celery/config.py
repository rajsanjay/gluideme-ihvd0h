# celery/config.py
# Version: Celery 5.3+
# Purpose: Celery configuration module for Transfer Requirements Management System

import os

# Broker and Backend URLs with secure defaults
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')

# Serialization settings
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']

# Timezone configuration
CELERY_ENABLE_UTC = True
CELERY_TIMEZONE = 'UTC'

def get_queue_config():
    """
    Returns comprehensive Celery queue configuration including task time limits,
    concurrency settings, and memory management.
    
    Returns:
        dict: Complete queue configuration settings
    """
    config = {
        # Broker and results configuration
        'broker_url': CELERY_BROKER_URL,
        'result_backend': CELERY_RESULT_BACKEND,
        
        # Task execution settings
        'task_time_limit': 3600,  # Hard limit: 1 hour
        'task_soft_time_limit': 3300,  # Soft limit: 55 minutes
        'task_default_queue': 'default',
        
        # Worker optimization settings
        'worker_prefetch_multiplier': 1,  # Prevent worker starvation
        'worker_max_tasks_per_child': 1000,  # Prevent memory leaks
        'worker_max_memory_per_child': 400000,  # 400MB memory limit
        
        # Task acknowledgment and retry settings
        'task_acks_late': True,  # Acknowledge after task completion
        'task_reject_on_worker_lost': True,  # Requeue tasks on worker failure
        'task_default_retry_delay': 180,  # 3 minutes retry delay
        'task_max_retries': 3,  # Maximum retry attempts
        
        # Queue definitions with priority levels
        'task_queues': {
            'requirements': {
                'routing_key': 'requirements.*',
                'queue_arguments': {
                    'x-max-priority': 10,
                    'x-message-ttl': 3600000,  # 1 hour TTL
                    'x-dead-letter-exchange': 'dlx'
                }
            },
            'validation': {
                'routing_key': 'validation.*',
                'queue_arguments': {
                    'x-max-priority': 8,
                    'x-message-ttl': 1800000,  # 30 minutes TTL
                    'x-dead-letter-exchange': 'dlx'
                }
            },
            'search': {
                'routing_key': 'search.*',
                'queue_arguments': {
                    'x-max-priority': 5,
                    'x-message-ttl': 900000,  # 15 minutes TTL
                    'x-dead-letter-exchange': 'dlx'
                }
            },
            'notifications': {
                'routing_key': 'notifications.*',
                'queue_arguments': {
                    'x-max-priority': 3,
                    'x-message-ttl': 3600000,  # 1 hour TTL
                    'x-dead-letter-exchange': 'dlx'
                }
            }
        },
        
        # Result backend settings
        'result_expires': 86400,  # Results expire after 24 hours
        'result_persistent': True,  # Persist results in backend
        
        # Task serialization
        'task_serializer': CELERY_TASK_SERIALIZER,
        'result_serializer': CELERY_RESULT_SERIALIZER,
        'accept_content': CELERY_ACCEPT_CONTENT,
        
        # Timezone settings
        'enable_utc': CELERY_ENABLE_UTC,
        'timezone': CELERY_TIMEZONE
    }
    
    return config

def get_task_routes():
    """
    Returns task routing configuration mapping tasks to specific queues with priority levels.
    
    Returns:
        dict: Task routing configuration with queue assignments and priority levels
    """
    return {
        # High-priority requirement processing tasks
        'requirements.process_transfer_requirements': {
            'queue': 'requirements',
            'priority': 10
        },
        'requirements.update_requirement_version': {
            'queue': 'requirements',
            'priority': 9
        },
        
        # Validation tasks
        'validation.validate_course_equivalency': {
            'queue': 'validation',
            'priority': 8
        },
        'validation.verify_prerequisites': {
            'queue': 'validation',
            'priority': 7
        },
        
        # Search-related tasks
        'search.index_requirements': {
            'queue': 'search',
            'priority': 5
        },
        'search.update_search_index': {
            'queue': 'search',
            'priority': 4
        },
        
        # Notification tasks
        'notifications.send_requirement_update': {
            'queue': 'notifications',
            'priority': 3
        },
        'notifications.send_validation_result': {
            'queue': 'notifications',
            'priority': 2
        },
        
        # Default routing for unspecified tasks
        '*': {
            'queue': 'default',
            'priority': 0
        }
    }