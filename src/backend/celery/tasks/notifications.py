"""
Celery tasks for handling asynchronous email notifications in the Transfer Requirements Management System.
Implements high-performance, reliable email delivery with comprehensive error handling and monitoring.

Version: 1.0.0
"""

import logging
from typing import Dict, List, Optional, Union
from uuid import UUID
from cachetools import TTLCache  # version: 5.0+
from celery import shared_task  # version: 5.3+
from celery.exceptions import MaxRetriesExceededError
from django.conf import settings
from django.utils import timezone

# Internal imports
from celery.app import app
from utils.aws import SESClient
from apps.users.models import User

# Configure logging
logger = logging.getLogger(__name__)

# Initialize AWS SES client
ses_client = SESClient()

# Cache for user data (TTL: 5 minutes, max 1000 entries)
user_cache = TTLCache(maxsize=1000, ttl=300)

# Constants
BATCH_SIZE = 50
MAX_RETRIES = 3
RETRY_DELAY = 300  # 5 minutes

@app.task(name='notifications.requirement_update', queue='notifications')
@app.task(bind=True, max_retries=3, default_retry_delay=300)
def send_requirement_update_notification(
    self,
    user_id: UUID,
    requirement_id: UUID,
    update_type: str,
    priority: Optional[str] = 'normal'
) -> Dict:
    """
    Send notification when transfer requirements are updated.

    Args:
        user_id: Target user's UUID
        requirement_id: Updated requirement's UUID
        update_type: Type of update (created/modified/deleted)
        priority: Email priority level

    Returns:
        Dict: Email send response with delivery metrics
    """
    try:
        # Get user from cache or database
        user = user_cache.get(str(user_id))
        if not user:
            try:
                user = User.objects.get(id=user_id)
                user_cache[str(user_id)] = user
            except User.DoesNotExist:
                logger.error(f"User not found: {user_id}")
                return {'status': 'failed', 'error': 'User not found'}

        # Check notification preferences
        if not user.notification_preferences.get('requirement_updates', True):
            logger.info(f"User {user_id} has disabled requirement update notifications")
            return {'status': 'skipped', 'reason': 'notifications_disabled'}

        # Validate email address
        if not ses_client.validate_email(user.email):
            logger.error(f"Invalid email address for user {user_id}: {user.email}")
            return {'status': 'failed', 'error': 'invalid_email'}

        # Prepare email data
        template_data = {
            'user_name': user.get_full_name(),
            'requirement_id': str(requirement_id),
            'update_type': update_type,
            'timestamp': timezone.now().isoformat()
        }

        # Send email with priority handling
        response = ses_client.send_email(
            to_addresses=[user.email],
            template_name='requirement_update_notification',
            template_data=template_data,
            from_address=settings.NOTIFICATION_FROM_EMAIL,
            configuration={'priority': priority}
        )

        # Log success metrics
        logger.info(
            "Requirement update notification sent",
            extra={
                'user_id': str(user_id),
                'requirement_id': str(requirement_id),
                'message_id': response.get('MessageId')
            }
        )

        return {
            'status': 'success',
            'message_id': response.get('MessageId'),
            'timestamp': timezone.now().isoformat()
        }

    except Exception as e:
        logger.error(
            f"Failed to send requirement update notification: {str(e)}",
            exc_info=True,
            extra={
                'user_id': str(user_id),
                'requirement_id': str(requirement_id)
            }
        )

        # Implement exponential backoff retry
        try:
            self.retry(countdown=self.request.retries * RETRY_DELAY)
        except MaxRetriesExceededError:
            return {
                'status': 'failed',
                'error': str(e),
                'retries_exhausted': True
            }

@app.task(name='notifications.validation_result', queue='notifications')
@app.task(bind=True, max_retries=3, default_retry_delay=300)
def send_validation_result_notification(
    self,
    user_id: UUID,
    validation_id: UUID,
    priority: Optional[str] = 'high'
) -> Dict:
    """
    Send notification for course validation results.

    Args:
        user_id: Target user's UUID
        validation_id: Validation result UUID
        priority: Email priority level

    Returns:
        Dict: Email send response with delivery metrics
    """
    try:
        # Get user from cache or database
        user = user_cache.get(str(user_id))
        if not user:
            try:
                user = User.objects.get(id=user_id)
                user_cache[str(user_id)] = user
            except User.DoesNotExist:
                logger.error(f"User not found: {user_id}")
                return {'status': 'failed', 'error': 'User not found'}

        # Check notification preferences
        if not user.notification_preferences.get('validation_results', True):
            logger.info(f"User {user_id} has disabled validation notifications")
            return {'status': 'skipped', 'reason': 'notifications_disabled'}

        # Validate email address
        if not ses_client.validate_email(user.email):
            logger.error(f"Invalid email address for user {user_id}: {user.email}")
            return {'status': 'failed', 'error': 'invalid_email'}

        # Prepare email data
        template_data = {
            'user_name': user.get_full_name(),
            'validation_id': str(validation_id),
            'timestamp': timezone.now().isoformat()
        }

        # Send email with high priority
        response = ses_client.send_email(
            to_addresses=[user.email],
            template_name='validation_result_notification',
            template_data=template_data,
            from_address=settings.NOTIFICATION_FROM_EMAIL,
            configuration={'priority': priority}
        )

        # Log success metrics
        logger.info(
            "Validation result notification sent",
            extra={
                'user_id': str(user_id),
                'validation_id': str(validation_id),
                'message_id': response.get('MessageId')
            }
        )

        return {
            'status': 'success',
            'message_id': response.get('MessageId'),
            'timestamp': timezone.now().isoformat()
        }

    except Exception as e:
        logger.error(
            f"Failed to send validation result notification: {str(e)}",
            exc_info=True,
            extra={
                'user_id': str(user_id),
                'validation_id': str(validation_id)
            }
        )

        try:
            self.retry(countdown=self.request.retries * RETRY_DELAY)
        except MaxRetriesExceededError:
            return {
                'status': 'failed',
                'error': str(e),
                'retries_exhausted': True
            }

@app.task(name='notifications.bulk_send', queue='notifications')
@app.task(bind=True, max_retries=3, default_retry_delay=300)
def send_bulk_notification(
    self,
    user_ids: List[UUID],
    subject: str,
    message: str,
    priority: Optional[str] = 'normal',
    batch_size: Optional[int] = BATCH_SIZE
) -> Dict:
    """
    Send optimized bulk notifications to multiple users.

    Args:
        user_ids: List of target user UUIDs
        subject: Email subject
        message: Email message content
        priority: Email priority level
        batch_size: Size of each batch

    Returns:
        Dict: Bulk email send response with metrics
    """
    try:
        results = {
            'successful': [],
            'failed': [],
            'skipped': []
        }

        # Process users in batches
        for i in range(0, len(user_ids), batch_size):
            batch = user_ids[i:i + batch_size]
            
            # Get users from database
            users = User.objects.filter(id__in=batch)
            
            # Filter users by notification preferences
            eligible_users = [
                user for user in users
                if user.notification_preferences.get('bulk_notifications', True)
            ]

            if not eligible_users:
                continue

            # Prepare recipient data
            recipients = [
                {'email': user.email, 'name': user.get_full_name()}
                for user in eligible_users
                if ses_client.validate_email(user.email)
            ]

            try:
                # Send bulk email
                response = ses_client.send_bulk_email(
                    recipients=recipients,
                    subject=subject,
                    message=message,
                    from_address=settings.NOTIFICATION_FROM_EMAIL,
                    configuration={'priority': priority}
                )

                # Track results
                results['successful'].extend([
                    {'user_id': str(user.id), 'email': user.email}
                    for user in eligible_users
                ])

            except Exception as batch_error:
                logger.error(
                    f"Batch send failed: {str(batch_error)}",
                    extra={'batch_size': len(recipients)}
                )
                results['failed'].extend([
                    {'user_id': str(user.id), 'error': str(batch_error)}
                    for user in eligible_users
                ])

        # Log overall metrics
        logger.info(
            "Bulk notification complete",
            extra={
                'total_successful': len(results['successful']),
                'total_failed': len(results['failed']),
                'total_skipped': len(results['skipped'])
            }
        )

        return {
            'status': 'completed',
            'metrics': {
                'successful': len(results['successful']),
                'failed': len(results['failed']),
                'skipped': len(results['skipped'])
            },
            'details': results,
            'timestamp': timezone.now().isoformat()
        }

    except Exception as e:
        logger.error(
            f"Bulk notification failed: {str(e)}",
            exc_info=True,
            extra={'total_users': len(user_ids)}
        )

        try:
            self.retry(countdown=self.request.retries * RETRY_DELAY)
        except MaxRetriesExceededError:
            return {
                'status': 'failed',
                'error': str(e),
                'retries_exhausted': True
            }