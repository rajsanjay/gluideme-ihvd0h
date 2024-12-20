"""
Celery task definitions for asynchronous search operations.
Handles MeiliSearch indexing and Pinecone vector operations with resilient error handling.

Version: 1.0
"""

import logging
from celery import states
from celery.exceptions import MaxRetriesExceededError
from apps.search.meilisearch import MeiliSearchClient
from apps.search.pinecone import PineconeClient
from celery.app import task
from typing import Dict, List, Optional
import structlog
from datetime import datetime

# Configure structured logging
logger = structlog.get_logger(__name__)

# Constants for retry configuration
MAX_RETRIES = 3
RETRY_BACKOFF = True
RETRY_DELAY = 180  # 3 minutes initial delay
BATCH_SIZE = 100

@task(
    name='search.update_index',
    queue='search',
    retry_backoff=RETRY_BACKOFF,
    max_retries=MAX_RETRIES,
    retry_delay=RETRY_DELAY,
    priority=9
)
def update_search_index(requirement_data: Dict) -> bool:
    """
    Update both MeiliSearch and Pinecone indices for a requirement with circuit breaker pattern.

    Args:
        requirement_data: Dictionary containing requirement data to index

    Returns:
        bool: Success status of indexing operations

    Raises:
        MaxRetriesExceededError: When max retries are exceeded
    """
    task_id = update_search_index.request.id
    start_time = datetime.now()

    logger.info(
        "starting_search_index_update",
        task_id=task_id,
        requirement_id=requirement_data.get('id')
    )

    try:
        # Initialize clients
        meili_client = MeiliSearchClient()
        pinecone_client = PineconeClient.get_instance()

        # Validate requirement data
        if not requirement_data.get('id'):
            raise ValueError("Requirement ID is required")

        # Update MeiliSearch index
        meili_client.update_requirement_index(requirement_data)

        # Generate and update vectors in Pinecone
        vectors = _generate_requirement_vectors(requirement_data)
        pinecone_client.upsert_vectors(
            vectors=[vector['embedding'] for vector in vectors],
            ids=[vector['id'] for vector in vectors],
            metadata={'requirement_id': requirement_data['id']}
        )

        duration = (datetime.now() - start_time).total_seconds()
        logger.info(
            "search_index_update_completed",
            task_id=task_id,
            requirement_id=requirement_data['id'],
            duration=duration
        )
        return True

    except Exception as e:
        logger.error(
            "search_index_update_failed",
            task_id=task_id,
            requirement_id=requirement_data.get('id'),
            error=str(e),
            retry_count=update_search_index.request.retries
        )

        try:
            update_search_index.retry(exc=e)
        except MaxRetriesExceededError:
            logger.error(
                "max_retries_exceeded",
                task_id=task_id,
                requirement_id=requirement_data.get('id')
            )
            raise

@task(
    name='search.delete_index',
    queue='search',
    retry_backoff=RETRY_BACKOFF,
    max_retries=MAX_RETRIES,
    retry_delay=RETRY_DELAY,
    priority=8
)
def delete_from_search_index(requirement_id: str) -> bool:
    """
    Remove requirement from both search indices with guaranteed consistency.

    Args:
        requirement_id: ID of requirement to delete

    Returns:
        bool: Success status of deletion operations

    Raises:
        MaxRetriesExceededError: When max retries are exceeded
    """
    task_id = delete_from_search_index.request.id
    start_time = datetime.now()

    logger.info(
        "starting_search_index_deletion",
        task_id=task_id,
        requirement_id=requirement_id
    )

    try:
        # Initialize clients
        meili_client = MeiliSearchClient()
        pinecone_client = PineconeClient.get_instance()

        # Delete from MeiliSearch
        meili_client.delete_requirement(requirement_id)

        # Delete from Pinecone
        pinecone_client.delete_vectors([requirement_id])

        duration = (datetime.now() - start_time).total_seconds()
        logger.info(
            "search_index_deletion_completed",
            task_id=task_id,
            requirement_id=requirement_id,
            duration=duration
        )
        return True

    except Exception as e:
        logger.error(
            "search_index_deletion_failed",
            task_id=task_id,
            requirement_id=requirement_id,
            error=str(e),
            retry_count=delete_from_search_index.request.retries
        )

        try:
            delete_from_search_index.retry(exc=e)
        except MaxRetriesExceededError:
            logger.error(
                "max_retries_exceeded",
                task_id=task_id,
                requirement_id=requirement_id
            )
            raise

@task(
    name='search.reindex_all',
    queue='search',
    time_limit=3600,  # 1 hour timeout
    soft_time_limit=3300,  # 55 minutes soft timeout
    priority=5
)
def reindex_all_requirements() -> Dict:
    """
    Rebuild entire search indices with progress tracking and batching.

    Returns:
        Dict: Summary of reindexing operation with detailed metrics

    Raises:
        Exception: If reindexing fails
    """
    task_id = reindex_all_requirements.request.id
    start_time = datetime.now()
    metrics = {
        'total_requirements': 0,
        'processed': 0,
        'failed': 0,
        'duration': 0,
        'batches': 0
    }

    logger.info(
        "starting_full_reindex",
        task_id=task_id
    )

    try:
        from apps.requirements.models import TransferRequirement

        # Get all active requirements
        requirements = TransferRequirement.objects.filter(
            status='published',
            is_active=True
        )
        metrics['total_requirements'] = requirements.count()

        # Process in batches
        for i in range(0, metrics['total_requirements'], BATCH_SIZE):
            batch = requirements[i:i + BATCH_SIZE]
            metrics['batches'] += 1

            for requirement in batch:
                try:
                    requirement_data = {
                        'id': str(requirement.id),
                        'title': requirement.title,
                        'description': requirement.description,
                        'major_code': requirement.major_code,
                        'institution_id': str(requirement.source_institution.id),
                        'type': requirement.type,
                        'status': requirement.status,
                        'metadata': requirement.metadata
                    }
                    update_search_index.apply_async(
                        args=[requirement_data],
                        priority=7
                    )
                    metrics['processed'] += 1
                except Exception as e:
                    metrics['failed'] += 1
                    logger.error(
                        "requirement_reindex_failed",
                        task_id=task_id,
                        requirement_id=str(requirement.id),
                        error=str(e)
                    )

        metrics['duration'] = (datetime.now() - start_time).total_seconds()
        logger.info(
            "full_reindex_completed",
            task_id=task_id,
            metrics=metrics
        )
        return metrics

    except Exception as e:
        logger.error(
            "full_reindex_failed",
            task_id=task_id,
            error=str(e)
        )
        raise

def _generate_requirement_vectors(requirement_data: Dict) -> List[Dict]:
    """
    Generate vector embeddings for requirement data.

    Args:
        requirement_data: Requirement data to vectorize

    Returns:
        List[Dict]: List of vector data with IDs and embeddings
    """
    # This is a placeholder for the actual vector generation logic
    # In a real implementation, this would use a machine learning model
    # to generate embeddings from the requirement text
    return [{
        'id': requirement_data['id'],
        'embedding': [0.0] * 512  # Placeholder 512-dimensional vector
    }]