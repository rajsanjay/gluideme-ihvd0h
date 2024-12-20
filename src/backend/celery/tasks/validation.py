"""
Celery tasks for handling asynchronous course validation operations.
Implements background processing for course validation, cache management, 
and batch validation operations.

Version: 1.0
"""

from datetime import timedelta
from django.utils import timezone  # v4.2+
from django.core.exceptions import ValidationError  # v4.2+
from django.db import transaction  # v4.2+
from apps.validation.models import ValidationRecord, ValidationCache
from celery.app import app

# Global constants
VALIDATION_CACHE_TTL = timedelta(hours=24)
MAX_BATCH_SIZE = 1000
RETRY_BACKOFF = True

@app.task(name='validation.validate_course',
         queue='validation',
         bind=True,
         max_retries=3,
         retry_backoff=True,
         retry_jitter=True)
def validate_course(self, course_id: str, requirement_id: str) -> dict:
    """
    Asynchronous task to validate a course against transfer requirements.
    
    Args:
        course_id: UUID of course to validate
        requirement_id: UUID of requirement to validate against
        
    Returns:
        dict: Validation results with status and metrics
    """
    try:
        with transaction.atomic():
            # Create or get validation record
            validation_record = ValidationRecord.objects.select_for_update().get_or_create(
                course_id=course_id,
                requirement_id=requirement_id
            )[0]

            # Check cache first
            cache_entry = ValidationCache.objects.filter(
                course_id=course_id,
                requirement_id=requirement_id
            ).first()

            if cache_entry and cache_entry.is_valid():
                return {
                    'status': 'valid',
                    'source': 'cache',
                    'results': cache_entry.results,
                    'accuracy_score': validation_record.accuracy_score
                }

            # Perform validation
            validation_results = validation_record.validate()

            # Update cache
            if cache_entry:
                cache_entry.refresh(validation_results)
            else:
                ValidationCache.objects.create(
                    course_id=course_id,
                    requirement_id=requirement_id,
                    results=validation_results,
                    expires_at=timezone.now() + VALIDATION_CACHE_TTL
                )

            return {
                'status': validation_record.status,
                'source': 'validation',
                'results': validation_results,
                'accuracy_score': validation_record.accuracy_score
            }

    except ValidationError as e:
        # Handle validation errors with retry
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=self.retry_backoff)
        return {
            'status': 'error',
            'error': str(e),
            'validation_errors': e.message_dict
        }

    except Exception as e:
        # Log and handle unexpected errors
        self.logger.error(f"Validation failed: {str(e)}", exc_info=True)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=self.retry_backoff)
        return {
            'status': 'error',
            'error': str(e)
        }

@app.task(name='validation.batch_validate_courses',
         queue='validation',
         bind=True,
         rate_limit='100/m')
def batch_validate_courses(self, course_ids: list, requirement_id: str) -> dict:
    """
    Asynchronous task to validate multiple courses in batch.
    
    Args:
        course_ids: List of course UUIDs to validate
        requirement_id: UUID of requirement to validate against
        
    Returns:
        dict: Batch validation results and metrics
    """
    if len(course_ids) > MAX_BATCH_SIZE:
        raise ValidationError(f"Batch size exceeds maximum of {MAX_BATCH_SIZE}")

    results = {
        'total': len(course_ids),
        'successful': 0,
        'failed': 0,
        'validation_results': {},
        'errors': {}
    }

    # Create subtasks for each course
    validation_tasks = []
    for course_id in course_ids:
        task = validate_course.s(course_id, requirement_id)
        validation_tasks.append(task)

    # Execute tasks in parallel with progress tracking
    for task_result in app.chunks(validation_tasks, 10)():
        course_id = task_result.args[0]
        if task_result.successful():
            results['successful'] += 1
            results['validation_results'][course_id] = task_result.result
        else:
            results['failed'] += 1
            results['errors'][course_id] = str(task_result.result)

    # Calculate aggregate metrics
    results['success_rate'] = (results['successful'] / results['total']) * 100
    results['completion_timestamp'] = timezone.now().isoformat()

    return results

@app.task(name='validation.cleanup_cache',
         queue='validation')
@app.periodic_task(run_every=timedelta(hours=24),
                  options={'expires': 3600})
def cleanup_validation_cache() -> dict:
    """
    Periodic task to clean up expired validation cache entries.
    
    Returns:
        dict: Cleanup statistics and metrics
    """
    try:
        stats = {
            'started_at': timezone.now().isoformat(),
            'entries_removed': 0,
            'space_reclaimed': 0
        }

        # Delete expired cache entries in batches
        expired_entries = ValidationCache.objects.filter(
            expires_at__lt=timezone.now()
        )
        
        total_size = sum(len(str(entry.results)) for entry in expired_entries)
        deleted_count = expired_entries.delete()[0]

        stats.update({
            'entries_removed': deleted_count,
            'space_reclaimed': total_size,
            'completed_at': timezone.now().isoformat()
        })

        return stats

    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }

@app.task(name='validation.revalidate_requirement',
         queue='validation',
         bind=True,
         priority=8)
def revalidate_requirement(self, requirement_id: str) -> dict:
    """
    Task to revalidate all courses for an updated requirement.
    
    Args:
        requirement_id: UUID of requirement to revalidate
        
    Returns:
        dict: Revalidation summary and metrics
    """
    try:
        with transaction.atomic():
            # Get all affected validation records
            validation_records = ValidationRecord.objects.filter(
                requirement_id=requirement_id
            ).select_for_update()

            # Invalidate cache entries
            ValidationCache.objects.filter(
                requirement_id=requirement_id
            ).delete()

            # Create batch validation tasks
            course_ids = list(validation_records.values_list('course_id', flat=True))
            
            if not course_ids:
                return {
                    'status': 'completed',
                    'message': 'No courses to revalidate',
                    'timestamp': timezone.now().isoformat()
                }

            # Execute batch validation
            batch_task = batch_validate_courses.delay(course_ids, requirement_id)
            
            return {
                'status': 'initiated',
                'courses_count': len(course_ids),
                'batch_task_id': batch_task.id,
                'timestamp': timezone.now().isoformat()
            }

    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }