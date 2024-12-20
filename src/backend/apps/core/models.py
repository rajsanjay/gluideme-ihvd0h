"""
Core Django models for the Transfer Requirements Management System.
Implements base models with versioning, audit logging, and validation mechanisms.

Version: 1.0
"""

from django.db import models
from django.utils import timezone
import uuid
from utils.validators import validate_course_code, validate_credits
from utils.exceptions import ValidationError
from typing import Dict, Any, Optional

class BaseModel(models.Model):
    """
    Abstract base model providing common fields and optimized query patterns.
    Implements soft deletion and metadata handling with PostgreSQL optimizations.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_index=True,
        help_text="Unique identifier for the record"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Timestamp when the record was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when the record was last updated"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Soft deletion status"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Flexible metadata storage"
    )

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['created_at', 'is_active']),
            models.Index(fields=['updated_at', 'is_active'])
        ]

    def save(self, force_insert=False, force_update=False, **kwargs):
        """
        Enhanced save method with validation and optimization.
        
        Args:
            force_insert (bool): Force an INSERT
            force_update (bool): Force an UPDATE
            **kwargs: Additional save parameters
            
        Returns:
            Self: Updated model instance
        """
        try:
            # Pre-save validation
            self.full_clean()
            
            # Update timestamp
            self.updated_at = timezone.now()
            
            # Optimize bulk operations
            if 'update_fields' in kwargs and 'updated_at' not in kwargs['update_fields']:
                kwargs['update_fields'].append('updated_at')
                
            return super().save(force_insert=force_insert, force_update=force_update, **kwargs)
            
        except Exception as e:
            raise ValidationError(
                message="Failed to save model instance",
                validation_errors={'model': str(e)}
            )

    def soft_delete(self) -> bool:
        """
        Implement soft deletion with cascading.
        
        Returns:
            bool: Deletion success status
        """
        try:
            self.is_active = False
            self.metadata['deleted_at'] = timezone.now().isoformat()
            self.save(update_fields=['is_active', 'metadata', 'updated_at'])
            return True
        except Exception as e:
            raise ValidationError(
                message="Failed to soft delete instance",
                validation_errors={'delete': str(e)}
            )

class VersionedModel(BaseModel):
    """
    Abstract model implementing temporal tables with version control.
    Provides comprehensive versioning with effective dating and chain tracking.
    """
    version = models.PositiveIntegerField(
        default=1,
        help_text="Version number of the record"
    )
    effective_from = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When this version becomes effective"
    )
    effective_to = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="When this version expires"
    )
    previous_version = models.UUIDField(
        null=True,
        blank=True,
        help_text="Reference to the previous version"
    )
    version_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Version-specific metadata"
    )
    change_reason = models.TextField(
        blank=True,
        help_text="Reason for version change"
    )

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['version', 'effective_from']),
            models.Index(fields=['effective_from', 'effective_to'])
        ]

    def create_new_version(self, data: Dict[str, Any], reason: str, 
                          effective_date: Optional[timezone.datetime] = None) -> 'VersionedModel':
        """
        Create new version with optimized chain management.
        
        Args:
            data: Updated field values
            reason: Reason for version change
            effective_date: When the new version becomes effective
            
        Returns:
            VersionedModel: New version instance
        """
        try:
            # Validate version chain
            if self.effective_to is not None:
                raise ValidationError(
                    message="Cannot create new version from expired record",
                    validation_errors={'version': 'Base version is expired'}
                )

            # Prepare new version
            new_version = self.__class__.objects.get(pk=self.pk)
            new_version.pk = uuid.uuid4()
            new_version.version = self.version + 1
            new_version.previous_version = self.pk
            new_version.effective_from = effective_date or timezone.now()
            new_version.change_reason = reason
            
            # Update fields
            for field, value in data.items():
                setattr(new_version, field, value)
            
            # Set version metadata
            new_version.version_metadata = {
                'created_from': str(self.pk),
                'change_reason': reason,
                'changed_fields': list(data.keys())
            }
            
            # Update old version's effective_to
            self.effective_to = new_version.effective_from
            self.save(update_fields=['effective_to', 'updated_at'])
            
            # Save new version
            new_version.save()
            return new_version
            
        except Exception as e:
            raise ValidationError(
                message="Failed to create new version",
                validation_errors={'version': str(e)}
            )

    def get_version_at(self, timestamp: timezone.datetime) -> Optional['VersionedModel']:
        """
        Retrieve version at specific point in time.
        
        Args:
            timestamp: Point in time to query
            
        Returns:
            VersionedModel: Version valid at timestamp
        """
        try:
            return self.__class__.objects.filter(
                models.Q(effective_from__lte=timestamp) &
                (models.Q(effective_to__gt=timestamp) | models.Q(effective_to__isnull=True))
            ).get()
        except self.__class__.DoesNotExist:
            return None

class AuditModel(BaseModel):
    """
    Abstract model implementing comprehensive audit logging.
    Tracks all changes with user attribution and categorization.
    """
    created_by = models.UUIDField(
        null=True,
        blank=True,
        help_text="User who created the record"
    )
    updated_by = models.UUIDField(
        null=True,
        blank=True,
        help_text="User who last updated the record"
    )
    change_log = models.JSONField(
        default=list,
        blank=True,
        help_text="Structured log of all changes"
    )
    change_category = models.CharField(
        max_length=50,
        blank=True,
        help_text="Category of the last change"
    )
    audit_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional audit context"
    )

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['created_by', 'updated_by']),
            models.Index(fields=['change_category'])
        ]

    def log_change(self, action: str, changes: Dict[str, Any], 
                   user_id: uuid.UUID, category: str) -> None:
        """
        Record detailed change in audit log.
        
        Args:
            action: Type of change
            changes: Changed field values
            user_id: User making the change
            category: Change category
        """
        try:
            # Format change entry
            change_entry = {
                'timestamp': timezone.now().isoformat(),
                'action': action,
                'user_id': str(user_id),
                'changes': changes,
                'category': category
            }
            
            # Update change log
            if isinstance(self.change_log, list):
                self.change_log.append(change_entry)
            else:
                self.change_log = [change_entry]
            
            # Update metadata
            self.updated_by = user_id
            self.change_category = category
            self.save(update_fields=['change_log', 'updated_by', 
                                   'change_category', 'updated_at'])
                                   
        except Exception as e:
            raise ValidationError(
                message="Failed to log change",
                validation_errors={'audit': str(e)}
            )