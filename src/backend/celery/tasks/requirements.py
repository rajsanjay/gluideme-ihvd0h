"""
Celery tasks for asynchronous processing of transfer requirements.
Implements comprehensive validation, indexing, and notifications with enhanced error handling.

Version: Celery 5.3+
"""

import logging
from celery import shared_task
from django.core.cache import cache
from django.utils import timezone
from typing import Dict, List, Optional, Any

from apps.requirements.models import TransferRequirement
from apps.search.meilisearch import MeiliSearchClient
from utils.exceptions import ValidationError

# Configure logging
logger = logging.getLogger(__name__)

# Initialize search client
search_client = MeiliSearchClient()

# Task configuration constants
BATCH_SIZE = 100
MAX_RETRIES = 3
VALIDATION_CACHE_TTL = 3600  # 1 hour
CLEANUP_BATCH_SIZE = 50

@shared_task(
    name='requirements.process_update',
    queue='requirements',
    max_retries=MAX_RETRIES,
    retry_backoff=True,
    rate_limit='100/m'
)
def process_requirement_update(requirement_id: str, options: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Process transfer requirement updates with comprehensive validation and indexing.
    
    Args:
        requirement_id: ID of requirement to process
        options: Optional processing configuration
        
    Returns:
        Dict: Processing results with status and metrics
    """
    logger.info(f"Processing requirement update: {requirement_id}", extra={
        'requirement_id': requirement_id,
        'options': options
    })
    
    try:
        # Initialize metrics
        metrics = {
            'start_time': timezone.now().isoformat(),
            'validation_count': 0,
            'index_updates': 0,
            'errors': []
        }
        
        # Retrieve requirement
        requirement = TransferRequirement.objects.get(pk=requirement_id)
        
        # Validate requirement data
        validation_results = _validate_requirement(requirement, options)
        metrics['validation_count'] += 1
        
        if not validation_results['valid']:
            raise ValidationError(
                message="Requirement validation failed",
                validation_errors=validation_results['errors']
            )
            
        # Update search index
        if options.get('update_index', True):
            _update_search_index(requirement)
            metrics['index_updates'] += 1
            
        # Cache validation results
        cache_key = f"requirement_validation:{requirement_id}"
        cache.set(cache_key, validation_results, timeout=VALIDATION_CACHE_TTL)
        
        # Update metrics
        metrics['end_time'] = timezone.now().isoformat()
        metrics['status'] = 'success'
        
        logger.info(f"Requirement processing completed: {requirement_id}", extra=metrics)
        return metrics
        
    except ValidationError as e:
        logger.error(f"Validation error for requirement {requirement_id}: {str(e)}", 
                    exc_info=True)
        metrics['errors'].append({
            'type': 'validation',
            'message': str(e),
            'details': e.validation_errors
        })
        raise
        
    except Exception as e:
        logger.error(f"Failed to process requirement {requirement_id}: {str(e)}", 
                    exc_info=True)
        metrics['errors'].append({
            'type': 'processing',
            'message': str(e)
        })
        raise

@shared_task(
    name='requirements.validate_courses',
    queue='requirements',
    max_retries=MAX_RETRIES,
    retry_backoff=True
)
def validate_requirement_courses(requirement_id: str, course_list: List[str], 
                              validation_options: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Validate courses against requirement rules with batch processing.
    
    Args:
        requirement_id: ID of requirement to validate against
        course_list: List of course IDs to validate
        validation_options: Optional validation configuration
        
    Returns:
        Dict: Validation results with detailed status
    """
    logger.info(f"Validating courses for requirement: {requirement_id}", extra={
        'requirement_id': requirement_id,
        'course_count': len(course_list)
    })
    
    try:
        requirement = TransferRequirement.objects.get(pk=requirement_id)
        results = {
            'start_time': timezone.now().isoformat(),
            'requirement_id': requirement_id,
            'total_courses': len(course_list),
            'valid_courses': 0,
            'invalid_courses': [],
            'validation_details': []
        }
        
        # Process courses in batches
        for i in range(0, len(course_list), BATCH_SIZE):
            batch = course_list[i:i + BATCH_SIZE]
            batch_results = requirement.validate_courses(batch)
            
            results['valid_courses'] += len(batch_results.get('valid_courses', []))
            results['invalid_courses'].extend(batch_results.get('invalid_courses', []))
            results['validation_details'].extend(batch_results.get('details', []))
            
        # Update completion metrics
        results['completion_percentage'] = (
            results['valid_courses'] / results['total_courses'] * 100
        )
        results['end_time'] = timezone.now().isoformat()
        
        logger.info(f"Course validation completed for requirement: {requirement_id}", 
                   extra=results)
        return results
        
    except Exception as e:
        logger.error(f"Course validation failed for requirement {requirement_id}: {str(e)}", 
                    exc_info=True)
        raise

@shared_task(
    name='requirements.update_index',
    queue='requirements',
    max_retries=MAX_RETRIES,
    retry_backoff=True
)
def update_search_index(requirement_id: str, index_options: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Update search index for requirement with validation and error handling.
    
    Args:
        requirement_id: ID of requirement to index
        index_options: Optional indexing configuration
        
    Returns:
        Dict: Indexing operation results
    """
    logger.info(f"Updating search index for requirement: {requirement_id}")
    
    try:
        requirement = TransferRequirement.objects.get(pk=requirement_id)
        
        # Validate requirement before indexing
        is_active, reasons = requirement.is_active()
        if not is_active:
            logger.warning(f"Skipping inactive requirement {requirement_id}: {reasons}")
            return {
                'status': 'skipped',
                'reason': reasons,
                'requirement_id': requirement_id
            }
            
        # Update search index
        search_client.update_requirement_index(requirement)
        
        results = {
            'status': 'success',
            'requirement_id': requirement_id,
            'timestamp': timezone.now().isoformat()
        }
        
        logger.info(f"Search index updated for requirement: {requirement_id}")
        return results
        
    except Exception as e:
        logger.error(f"Failed to update search index for requirement {requirement_id}: {str(e)}", 
                    exc_info=True)
        raise

@shared_task(
    name='requirements.cleanup',
    queue='requirements',
    max_retries=MAX_RETRIES,
    retry_backoff=True
)
def cleanup_archived_requirements(requirement_ids: List[str], 
                               cleanup_options: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Clean up archived requirements with batch processing and verification.
    
    Args:
        requirement_ids: List of requirement IDs to clean up
        cleanup_options: Optional cleanup configuration
        
    Returns:
        Dict: Cleanup operation results
    """
    logger.info(f"Starting cleanup for {len(requirement_ids)} requirements")
    
    results = {
        'start_time': timezone.now().isoformat(),
        'total_requirements': len(requirement_ids),
        'processed': 0,
        'errors': [],
        'deleted_from_index': []
    }
    
    try:
        # Process in batches
        for i in range(0, len(requirement_ids), CLEANUP_BATCH_SIZE):
            batch = requirement_ids[i:i + CLEANUP_BATCH_SIZE]
            
            for req_id in batch:
                try:
                    # Remove from search index
                    search_client.delete_requirement(req_id)
                    results['deleted_from_index'].append(req_id)
                    results['processed'] += 1
                    
                except Exception as e:
                    results['errors'].append({
                        'requirement_id': req_id,
                        'error': str(e)
                    })
                    
        results['end_time'] = timezone.now().isoformat()
        results['success_rate'] = (results['processed'] / results['total_requirements'] * 100)
        
        logger.info(f"Cleanup completed. Processed {results['processed']} requirements")
        return results
        
    except Exception as e:
        logger.error(f"Cleanup operation failed: {str(e)}", exc_info=True)
        raise

def _validate_requirement(requirement: TransferRequirement, 
                        options: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Internal helper for comprehensive requirement validation.
    
    Args:
        requirement: TransferRequirement instance to validate
        options: Optional validation configuration
        
    Returns:
        Dict: Validation results
    """
    try:
        requirement.full_clean()
        is_active, reasons = requirement.is_active()
        
        return {
            'valid': is_active,
            'requirement_id': str(requirement.id),
            'validation_timestamp': timezone.now().isoformat(),
            'errors': [] if is_active else reasons
        }
        
    except ValidationError as e:
        return {
            'valid': False,
            'requirement_id': str(requirement.id),
            'validation_timestamp': timezone.now().isoformat(),
            'errors': e.validation_errors
        }

def _update_search_index(requirement: TransferRequirement) -> None:
    """
    Internal helper for search index updates with error handling.
    
    Args:
        requirement: TransferRequirement instance to index
    """
    try:
        search_client.update_requirement_index(requirement)
    except Exception as e:
        logger.error(f"Search index update failed for requirement {requirement.id}: {str(e)}", 
                    exc_info=True)
        raise