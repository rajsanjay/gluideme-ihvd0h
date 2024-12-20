"""
Django models for managing validation records and results for transfer requirements.
Implements comprehensive validation tracking, caching, and progress monitoring.

Version: 1.0
"""

from django.db import models  # v4.2+
from django.utils import timezone  # v4.2+
from django.core.exceptions import ValidationError  # v4.2+
from django.core.cache import cache  # v4.2+
from apps.core.models import BaseModel
from apps.courses.models import Course
from apps.requirements.models import TransferRequirement
from typing import Dict, Optional

# Validation status choices with comprehensive states
VALIDATION_STATUS = (
    ('pending', 'Pending'),
    ('valid', 'Valid'), 
    ('invalid', 'Invalid'),
    ('error', 'Error'),
    ('in_progress', 'In Progress')
)

# Cache timeout for validation results (24 hours)
CACHE_TIMEOUT = 86400

class ValidationRecord(BaseModel):
    """
    Enhanced model for tracking validation attempts, results and progress 
    with comprehensive metadata tracking.
    """
    requirement = models.ForeignKey(
        'requirements.TransferRequirement',
        on_delete=models.CASCADE,
        related_name='validations',
        help_text="Transfer requirement being validated"
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='validations',
        help_text="Course being validated"
    )
    status = models.CharField(
        max_length=20,
        choices=VALIDATION_STATUS,
        default='pending',
        db_index=True,
        help_text="Current validation status"
    )
    results = models.JSONField(
        default=dict,
        help_text="Detailed validation results"
    )
    validated_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When validation was performed"
    )
    valid_until = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Validation result expiration"
    )
    metadata = models.JSONField(
        default=dict,
        help_text="Validation progress and tracking data"
    )
    accuracy_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        db_index=True,
        help_text="Validation accuracy percentage"
    )

    class Meta:
        db_table = 'validation_records'
        unique_together = [['requirement', 'course']]
        indexes = [
            models.Index(fields=['status', 'validated_at']),
            models.Index(fields=['accuracy_score']),
            models.Index(fields=['requirement', 'status'])
        ]
        ordering = ['-validated_at']
        verbose_name = 'Validation Record'
        verbose_name_plural = 'Validation Records'

    def __str__(self) -> str:
        return f"Validation: {self.requirement.major_code} - {self.course.code}"

    def validate(self) -> Dict:
        """
        Perform comprehensive validation with progress tracking and accuracy metrics.
        
        Returns:
            Dict: Validation results with status and metrics
        """
        try:
            # Update status and initialize progress
            self.status = 'in_progress'
            self.metadata['progress'] = 0
            self.save(update_fields=['status', 'metadata'])

            # Check course transfer validity
            course_valid = self.course.is_valid_for_transfer(
                timezone.now(),
                self.requirement.target_institution
            )
            self.metadata['progress'] = 25
            self.save(update_fields=['metadata'])

            # Apply requirement validation rules
            requirement_valid = self.requirement.validate_courses([self.course])
            self.metadata['progress'] = 50
            self.save(update_fields=['metadata'])

            # Calculate validation accuracy
            self.accuracy_score = 100.0 if (course_valid and requirement_valid['valid']) else 0.0
            self.metadata['progress'] = 75
            self.save(update_fields=['metadata', 'accuracy_score'])

            # Prepare validation results
            validation_results = {
                'course_valid': course_valid,
                'requirement_valid': requirement_valid,
                'accuracy_score': self.accuracy_score,
                'validation_timestamp': timezone.now().isoformat()
            }

            # Update record with results
            self.results = validation_results
            self.status = 'valid' if (course_valid and requirement_valid['valid']) else 'invalid'
            self.valid_until = timezone.now() + timezone.timedelta(days=1)
            self.metadata['progress'] = 100
            self.save()

            # Cache validation results
            cache_key = f"validation:{self.requirement.pk}:{self.course.pk}"
            cache.set(cache_key, validation_results, timeout=CACHE_TIMEOUT)

            return validation_results

        except Exception as e:
            self.status = 'error'
            self.results = {'error': str(e)}
            self.save()
            raise ValidationError(f"Validation failed: {str(e)}")

    def is_valid(self, date: Optional[timezone.datetime] = None, 
                 min_accuracy: Optional[float] = 99.99) -> bool:
        """
        Check validation validity with accuracy threshold.
        
        Args:
            date: Optional date to check validity
            min_accuracy: Minimum required accuracy score
            
        Returns:
            bool: Validation validity status
        """
        date = date or timezone.now()
        
        # Check basic validity conditions
        if self.status != 'valid':
            return False
            
        if not (self.validated_at <= date and 
                (not self.valid_until or date <= self.valid_until)):
            return False
            
        # Check accuracy threshold
        if self.accuracy_score is None or self.accuracy_score < min_accuracy:
            return False
            
        return True

class ValidationCache(BaseModel):
    """
    Enhanced model for caching validation results with performance optimization.
    """
    requirement = models.ForeignKey(
        'requirements.TransferRequirement',
        on_delete=models.CASCADE,
        related_name='validation_cache',
        help_text="Cached requirement"
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='validation_cache',
        help_text="Cached course"
    )
    cache_key = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Unique cache identifier"
    )
    results = models.JSONField(
        help_text="Cached validation results"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Cache entry creation time"
    )
    expires_at = models.DateTimeField(
        db_index=True,
        help_text="Cache entry expiration"
    )
    hit_count = models.PositiveIntegerField(
        default=0,
        db_index=True,
        help_text="Number of cache hits"
    )

    class Meta:
        db_table = 'validation_cache'
        indexes = [
            models.Index(fields=['cache_key', 'expires_at']),
            models.Index(fields=['hit_count']),
            models.Index(fields=['requirement', 'course'])
        ]
        ordering = ['-created_at']
        verbose_name = 'Validation Cache'
        verbose_name_plural = 'Validation Caches'

    def __str__(self) -> str:
        return f"Cache: {self.requirement.major_code} - {self.course.code}"

    def is_valid(self) -> bool:
        """
        Check cache validity with hit tracking.
        
        Returns:
            bool: Cache validity status
        """
        now = timezone.now()
        
        # Check expiration
        if now >= self.expires_at:
            return False
            
        # Verify requirement and course are still active
        if not (self.requirement.is_active() and self.course.is_active):
            return False
            
        # Increment hit count
        self.hit_count += 1
        self.save(update_fields=['hit_count'])
        
        return True

    def refresh(self, results: Dict) -> None:
        """
        Refresh cache entry with new results and Redis integration.
        
        Args:
            results: New validation results
        """
        # Update cache entry
        self.results = results
        self.expires_at = timezone.now() + timezone.timedelta(days=1)
        self.hit_count = 0
        
        # Update Redis cache
        cache_key = f"validation:{self.requirement.pk}:{self.course.pk}"
        cache.set(cache_key, results, timeout=CACHE_TIMEOUT)
        
        self.save()