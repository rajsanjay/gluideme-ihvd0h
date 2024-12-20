"""
Django models for managing transfer requirements between institutions.
Implements comprehensive requirement management with validation, versioning, and accuracy tracking.

Version: 1.0
"""

from django.db import models  # v4.2+
from django.utils import timezone  # v4.2+
from django.core.exceptions import ValidationError  # v4.2+
from django.core.cache import cache  # v4.2+
from apps.core.models import BaseModel, VersionedModel
from apps.courses.models import Course
from apps.institutions.models import Institution
from utils.validators import validate_requirement_rules
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Global constants for model choices
REQUIREMENT_STATUS = (
    ('draft', 'Draft'),
    ('published', 'Published'),
    ('archived', 'Archived')
)

REQUIREMENT_TYPES = (
    ('major', 'Major Requirements'),
    ('general', 'General Education'),
    ('prerequisite', 'Prerequisites')
)

# Cache TTL for validation results
VALIDATION_CACHE_TTL = 3600  # 1 hour

class TransferRequirement(VersionedModel):
    """
    Comprehensive model for managing transfer requirements between institutions.
    Implements validation, versioning, and accuracy tracking with caching.
    """
    source_institution = models.ForeignKey(
        'institutions.Institution',
        on_delete=models.CASCADE,
        related_name='source_requirements',
        help_text="Source institution for transfer requirement"
    )
    target_institution = models.ForeignKey(
        'institutions.Institution',
        on_delete=models.CASCADE,
        related_name='target_requirements',
        help_text="Target institution for transfer requirement"
    )
    major_code = models.CharField(
        max_length=20,
        db_index=True,
        help_text="Major code for requirement"
    )
    title = models.CharField(
        max_length=200,
        help_text="Descriptive title for requirement"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed requirement description"
    )
    type = models.CharField(
        max_length=20,
        choices=REQUIREMENT_TYPES,
        help_text="Type of transfer requirement"
    )
    rules = models.JSONField(
        default=dict,
        help_text="Structured validation rules"
    )
    metadata = models.JSONField(
        default=dict,
        help_text="Version-specific metadata"
    )
    status = models.CharField(
        max_length=20,
        choices=REQUIREMENT_STATUS,
        default='draft',
        db_index=True,
        help_text="Current requirement status"
    )
    effective_date = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When requirement becomes effective"
    )
    expiration_date = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="When requirement expires"
    )
    validation_accuracy = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.0,
        help_text="Calculated validation accuracy percentage"
    )

    class Meta:
        db_table = 'transfer_requirements'
        unique_together = [['source_institution', 'target_institution', 'major_code']]
        indexes = [
            models.Index(fields=['major_code', 'status']),
            models.Index(fields=['effective_date', 'expiration_date']),
            models.Index(fields=['source_institution', 'target_institution'])
        ]
        ordering = ['-effective_date']
        verbose_name = 'Transfer Requirement'
        verbose_name_plural = 'Transfer Requirements'

    def __str__(self) -> str:
        return f"{self.source_institution.code} → {self.target_institution.code}: {self.major_code}"

    def clean(self) -> None:
        """
        Comprehensive validation of requirement data with enhanced error checking.
        Validates rules schema, metadata, dates, and institutional relationships.
        """
        try:
            # Validate rules schema and structure
            validate_requirement_rules(self.rules)

            # Validate metadata format
            required_metadata = {'version_notes', 'reviewer_id', 'approval_date'}
            if not all(field in self.metadata for field in required_metadata):
                raise ValidationError({
                    'metadata': f"Missing required metadata fields: {required_metadata}"
                })

            # Validate date ranges
            if self.expiration_date and self.effective_date >= self.expiration_date:
                raise ValidationError({
                    'expiration_date': "Expiration date must be after effective date"
                })

            # Validate institutional relationship
            if not self.source_institution.validate_articulation_agreement(
                self.target_institution
            ):
                raise ValidationError({
                    'institutions': "No valid articulation agreement exists between institutions"
                })

            # Validate course prerequisites
            self._validate_course_prerequisites()

        except ValidationError as e:
            logger.error(f"Requirement validation failed: {str(e)}", exc_info=True)
            raise

        except Exception as e:
            logger.error(f"Unexpected validation error: {str(e)}", exc_info=True)
            raise ValidationError({
                'validation': f"Requirement validation failed: {str(e)}"
            })

    def _validate_course_prerequisites(self) -> None:
        """
        Validate course prerequisite chains for consistency and cycles.
        """
        visited_courses = set()
        
        def check_prerequisites(course_code: str, path: List[str]) -> None:
            if course_code in path:
                raise ValidationError({
                    'prerequisites': f"Circular prerequisite dependency detected: {' -> '.join(path)}"
                })
            
            path.append(course_code)
            prerequisites = self.rules.get('prerequisites', {}).get(course_code, [])
            
            for prereq_code in prerequisites:
                check_prerequisites(prereq_code, path.copy())

        for course_code in self.rules.get('courses', []):
            check_prerequisites(course_code, [])

    def is_active(self, date: Optional[timezone.datetime] = None) -> Tuple[bool, List[str]]:
        """
        Check if requirement is currently active with caching support.
        
        Args:
            date: Optional date to check validity
            
        Returns:
            Tuple[bool, List[str]]: Active status and reasons
        """
        date = date or timezone.now()
        cache_key = f"requirement_active:{self.pk}:{date.isoformat()}"
        cached_result = cache.get(cache_key)

        if cached_result is not None:
            return cached_result

        reasons = []

        # Check status
        if self.status != 'published':
            reasons.append(f"Requirement not published (status: {self.status})")

        # Check date validity
        if not (self.effective_date <= date and 
                (not self.expiration_date or date <= self.expiration_date)):
            reasons.append("Requirement not valid for specified date")

        result = (len(reasons) == 0, reasons)
        cache.set(cache_key, result, timeout=VALIDATION_CACHE_TTL)
        return result

    def validate_courses(self, course_list: List[Course]) -> Dict[str, Any]:
        """
        Enhanced course validation against requirement rules with accuracy tracking.
        
        Args:
            course_list: List of courses to validate
            
        Returns:
            Dict: Comprehensive validation results
        """
        cache_key = f"requirement_validation:{self.pk}:{':'.join(str(c.pk) for c in course_list)}"
        cached_result = cache.get(cache_key)

        if cached_result is not None:
            return cached_result

        validation_results = {
            'valid': True,
            'completion_percentage': 0.0,
            'missing_requirements': [],
            'invalid_courses': [],
            'prerequisite_issues': [],
            'validation_timestamp': timezone.now().isoformat()
        }

        try:
            # Validate individual courses
            for course in course_list:
                if not course.is_valid_for_transfer(
                    timezone.now(), self.target_institution
                ):
                    validation_results['invalid_courses'].append(course.code)
                    validation_results['valid'] = False

            # Validate against requirement rules
            required_courses = set(self.rules.get('courses', []))
            submitted_courses = {c.code for c in course_list}
            
            # Check missing requirements
            missing = required_courses - submitted_courses
            if missing:
                validation_results['missing_requirements'].extend(list(missing))
                validation_results['valid'] = False

            # Validate prerequisites
            for course in course_list:
                if not course.validate_prerequisites(course_list):
                    validation_results['prerequisite_issues'].append(course.code)
                    validation_results['valid'] = False

            # Calculate completion percentage
            if required_courses:
                validation_results['completion_percentage'] = (
                    len(required_courses.intersection(submitted_courses)) / 
                    len(required_courses) * 100
                )

            # Update validation accuracy metrics
            self._update_validation_accuracy(validation_results)

            # Cache results
            cache.set(cache_key, validation_results, timeout=VALIDATION_CACHE_TTL)
            return validation_results

        except Exception as e:
            logger.error(f"Course validation failed: {str(e)}", exc_info=True)
            validation_results['valid'] = False
            validation_results['error'] = str(e)
            return validation_results

    def _update_validation_accuracy(self, validation_results: Dict[str, Any]) -> None:
        """
        Update validation accuracy metrics based on validation results.
        
        Args:
            validation_results: Results from course validation
        """
        try:
            # Calculate accuracy based on validation success
            total_validations = self.metadata.get('validation_count', 0) + 1
            current_accuracy = self.validation_accuracy or 0.0
            
            # Weight new validation result
            validation_weight = 1 / total_validations
            historical_weight = 1 - validation_weight
            
            new_accuracy = (
                (current_accuracy * historical_weight) +
                (100.0 if validation_results['valid'] else 0.0) * validation_weight
            )

            # Update metrics
            self.validation_accuracy = round(new_accuracy, 2)
            self.metadata['validation_count'] = total_validations
            self.metadata['last_validation'] = validation_results['validation_timestamp']
            
            self.save(update_fields=['validation_accuracy', 'metadata'])

        except Exception as e:
            logger.error(f"Failed to update validation accuracy: {str(e)}", exc_info=True)