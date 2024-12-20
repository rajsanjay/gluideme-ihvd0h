"""
Django models for managing course data in the Transfer Requirements Management System.
Implements comprehensive course data models with enhanced validation and relationship tracking.

Version: 1.0
"""

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from apps.core.models import BaseModel
from apps.institutions.models import Institution
from utils.validators import (
    validate_course_code,
    validate_credits,
    validate_metadata_schema
)
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Course status choices with comprehensive states
COURSE_STATUS = (
    ('active', 'Active'),
    ('inactive', 'Inactive'),
    ('pending', 'Pending Review'),
    ('archived', 'Archived')
)

# Metadata schema for course additional data
METADATA_SCHEMA = {
    'type': 'object',
    'properties': {
        'delivery_mode': {'type': 'string', 'enum': ['in_person', 'online', 'hybrid']},
        'prerequisites_description': {'type': 'string'},
        'learning_outcomes': {'type': 'array', 'items': {'type': 'string'}},
        'additional_requirements': {'type': 'object'},
        'transfer_agreements': {'type': 'array', 'items': {'type': 'string'}}
    },
    'required': ['delivery_mode', 'learning_outcomes']
}

class Course(BaseModel):
    """
    Comprehensive model representing an academic course with enhanced validation 
    and relationship tracking.
    """
    institution = models.ForeignKey(
        'institutions.Institution',
        on_delete=models.CASCADE,
        related_name='courses',
        db_index=True,
        help_text="Institution offering the course"
    )
    code = models.CharField(
        max_length=20,
        validators=[validate_course_code],
        help_text="Unique course code within institution"
    )
    name = models.CharField(
        max_length=200,
        help_text="Official course name"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed course description"
    )
    credits = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[validate_credits],
        help_text="Credit units for the course"
    )
    prerequisites = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        through='CoursePrerequisite',
        help_text="Required prerequisite courses"
    )
    metadata = models.JSONField(
        default=dict,
        validators=[validate_metadata_schema],
        help_text="Additional course metadata"
    )
    status = models.CharField(
        max_length=20,
        choices=COURSE_STATUS,
        default='active',
        db_index=True,
        help_text="Current course status"
    )
    valid_from = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="Course validity start date"
    )
    valid_to = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Course validity end date"
    )
    last_validated = models.DateTimeField(
        auto_now=True,
        help_text="Last validation timestamp"
    )
    validation_errors = models.JSONField(
        default=list,
        help_text="List of validation errors"
    )

    class Meta:
        db_table = 'courses'
        unique_together = [['institution', 'code']]
        ordering = ['institution', 'code']
        indexes = [
            models.Index(fields=['status', 'valid_from', 'valid_to']),
            models.Index(fields=['last_validated']),
            models.Index(fields=['institution', 'status'])
        ]
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'

    def __str__(self) -> str:
        return f"{self.institution.code} - {self.code}: {self.name}"

    def clean(self) -> None:
        """
        Comprehensive validation of course data with enhanced error checking.
        """
        try:
            # Validate course code format
            validate_course_code(self.code)

            # Validate credits value
            validate_credits(self.credits)

            # Validate metadata schema
            validate_metadata_schema(self.metadata)

            # Validate date ranges
            if self.valid_to and self.valid_from >= self.valid_to:
                raise ValidationError({
                    'valid_to': "End date must be after start date"
                })

            # Validate prerequisite relationships
            self._validate_prerequisites()

            # Clear validation errors if all checks pass
            self.validation_errors = []

        except ValidationError as e:
            self.validation_errors = e.message_dict
            raise

        except Exception as e:
            logger.error(f"Course validation failed: {str(e)}", exc_info=True)
            raise ValidationError({
                'validation': f"Course validation failed: {str(e)}"
            })

    def _validate_prerequisites(self) -> None:
        """
        Validate prerequisite relationships for cycles and consistency.
        """
        visited = set()
        
        def check_cycle(course, path):
            if course.id in path:
                raise ValidationError({
                    'prerequisites': f"Circular dependency detected: {' -> '.join(path)}"
                })
            path.add(course.id)
            for prereq in course.prerequisites.all():
                check_cycle(prereq, path.copy())

        check_cycle(self, set())

    @transaction.atomic
    def is_valid_for_transfer(self, date: timezone.datetime, 
                            target_institution: Institution) -> Tuple[bool, List[str]]:
        """
        Enhanced transfer validity checking with comprehensive validation.
        
        Args:
            date: Date to check validity
            target_institution: Target institution for transfer
            
        Returns:
            Tuple[bool, List[str]]: Validity status and reasons
        """
        reasons = []

        # Check course status
        if self.status != 'active':
            reasons.append(f"Course is not active (status: {self.status})")

        # Verify date within validity period
        if not (self.valid_from <= date and 
                (not self.valid_to or date <= self.valid_to)):
            reasons.append("Course not valid for specified date")

        # Check prerequisites validity
        for prereq in self.prerequisites.all():
            valid, prereq_reasons = prereq.is_valid_for_transfer(
                date, target_institution
            )
            if not valid:
                reasons.extend([f"Prerequisite {prereq.code}: {r}" for r in prereq_reasons])

        # Verify institutional agreements
        if not self._verify_institutional_agreement(target_institution):
            reasons.append("No valid transfer agreement exists")

        return len(reasons) == 0, reasons

    def _verify_institutional_agreement(self, target_institution: Institution) -> bool:
        """
        Verify existence of valid transfer agreement between institutions.
        
        Args:
            target_institution: Target institution
            
        Returns:
            bool: Agreement validity status
        """
        return CourseEquivalency.objects.filter(
            Q(source_course=self, target_course__institution=target_institution) |
            Q(target_course=self, source_course__institution=target_institution),
            validation_status='approved'
        ).exists()

    def get_equivalent_courses(self, institution: Institution,
                             date: Optional[timezone.datetime] = None) -> models.QuerySet:
        """
        Get equivalent courses with caching and filtering.
        
        Args:
            institution: Target institution
            date: Optional date filter
            
        Returns:
            QuerySet: Filtered equivalent courses
        """
        equivalencies = CourseEquivalency.objects.filter(
            Q(source_course=self, target_course__institution=institution) |
            Q(target_course=self, source_course__institution=institution)
        )

        if date:
            equivalencies = equivalencies.filter(
                Q(effective_date__lte=date),
                Q(expiration_date__isnull=True) | Q(expiration_date__gt=date)
            )

        return equivalencies.select_related('source_course', 'target_course')

class CourseEquivalency(BaseModel):
    """
    Enhanced model for managing course equivalencies with temporal validity.
    """
    source_course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='source_equivalencies',
        help_text="Source course in equivalency"
    )
    target_course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='target_equivalencies',
        help_text="Target course in equivalency"
    )
    effective_date = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When equivalency becomes effective"
    )
    expiration_date = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="When equivalency expires"
    )
    metadata = models.JSONField(
        default=dict,
        validators=[validate_metadata_schema],
        help_text="Additional equivalency metadata"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about equivalency"
    )
    validation_status = models.CharField(
        max_length=20,
        choices=(
            ('pending', 'Pending Review'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('expired', 'Expired')
        ),
        default='pending',
        help_text="Current validation status"
    )
    last_reviewed = models.DateTimeField(
        auto_now=True,
        help_text="Last review timestamp"
    )
    reviewed_by = models.ForeignKey(
        'users.User',
        null=True,
        on_delete=models.SET_NULL,
        help_text="User who last reviewed"
    )

    class Meta:
        db_table = 'course_equivalencies'
        unique_together = [['source_course', 'target_course']]
        indexes = [
            models.Index(fields=['effective_date', 'expiration_date']),
            models.Index(fields=['validation_status', 'last_reviewed'])
        ]
        verbose_name = 'Course Equivalency'
        verbose_name_plural = 'Course Equivalencies'

    def __str__(self) -> str:
        return f"{self.source_course.code} ⟷ {self.target_course.code}"

    def clean(self) -> None:
        """
        Validate equivalency data with comprehensive checks.
        """
        if self.source_course.institution == self.target_course.institution:
            raise ValidationError({
                'institution': "Source and target courses must be from different institutions"
            })

        if self.expiration_date and self.effective_date >= self.expiration_date:
            raise ValidationError({
                'expiration_date': "Expiration date must be after effective date"
            })

    def is_active(self, date: timezone.datetime = None) -> Tuple[bool, List[str]]:
        """
        Check equivalency validity with comprehensive validation.
        
        Args:
            date: Optional date to check validity
            
        Returns:
            Tuple[bool, List[str]]: Validity status and reasons
        """
        date = date or timezone.now()
        reasons = []

        # Check validation status
        if self.validation_status != 'approved':
            reasons.append(f"Equivalency not approved (status: {self.validation_status})")

        # Check date validity
        if not (self.effective_date <= date and 
                (not self.expiration_date or date <= self.expiration_date)):
            reasons.append("Equivalency not valid for specified date")

        # Check course validity
        source_valid, source_reasons = self.source_course.is_valid_for_transfer(
            date, self.target_course.institution
        )
        if not source_valid:
            reasons.extend([f"Source course: {r}" for r in source_reasons])

        target_valid, target_reasons = self.target_course.is_valid_for_transfer(
            date, self.source_course.institution
        )
        if not target_valid:
            reasons.extend([f"Target course: {r}" for r in target_reasons])

        return len(reasons) == 0, reasons