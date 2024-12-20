"""
Django models for managing institution data in the Transfer Requirements Management System.
Implements comprehensive institution and agreement models with versioning support.

Version: 1.0
"""

from django.db import models  # v4.2+
from django.utils import timezone  # v4.2+
from django.core.exceptions import ValidationError  # v4.2+
from django.core.cache import cache  # v4.2+
from apps.core.models import BaseModel, VersionedModel
from utils.validators import validate_institution_type
from typing import Dict, Any, List, Optional
import uuid

# Institution type choices with comprehensive options
INSTITUTION_TYPES = (
    ('university', 'University'),
    ('community_college', 'Community College'),
    ('private', 'Private Institution'),
    ('technical', 'Technical Institute'),
    ('online', 'Online Institution')
)

# Institution status choices for lifecycle management
INSTITUTION_STATUS = (
    ('active', 'Active'),
    ('inactive', 'Inactive'),
    ('pending', 'Pending Review'),
    ('suspended', 'Suspended'),
    ('archived', 'Archived')
)

# Agreement types for institutional relationships
AGREEMENT_TYPES = (
    ('articulation', 'Articulation Agreement'),
    ('partnership', 'Partnership'),
    ('exchange', 'Exchange Program'),
    ('dual_degree', 'Dual Degree')
)

def cache_model(cls):
    """
    Decorator for model-level caching with automatic invalidation.
    """
    original_save = cls.save
    original_delete = cls.delete

    def save_with_cache(self, *args, **kwargs):
        result = original_save(self, *args, **kwargs)
        cache.delete(f"institution:{self.pk}")
        return result

    def delete_with_cache(self, *args, **kwargs):
        cache.delete(f"institution:{self.pk}")
        return original_delete(self, *args, **kwargs)

    cls.save = save_with_cache
    cls.delete = delete_with_cache
    return cls

@cache_model
class Institution(VersionedModel):
    """
    Enhanced model representing an educational institution with comprehensive 
    validation and performance optimizations.
    """
    name = models.CharField(
        max_length=200,
        db_index=True,
        help_text="Official institution name"
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text="Unique institution code"
    )
    type = models.CharField(
        max_length=50,
        choices=INSTITUTION_TYPES,
        db_index=True,
        help_text="Institution classification"
    )
    status = models.CharField(
        max_length=20,
        choices=INSTITUTION_STATUS,
        default='active',
        db_index=True,
        help_text="Current operational status"
    )
    contact_info = models.JSONField(
        default=dict,
        help_text="Structured contact information"
    )
    address = models.JSONField(
        default=dict,
        help_text="Physical and mailing addresses"
    )
    metadata = models.JSONField(
        default=dict,
        help_text="Additional institution metadata"
    )
    website = models.URLField(
        blank=True,
        help_text="Official institution website"
    )
    accreditation = models.JSONField(
        default=dict,
        help_text="Accreditation details and status"
    )
    last_verified = models.DateTimeField(
        auto_now=True,
        help_text="Last verification timestamp"
    )

    class Meta:
        db_table = 'institutions'
        ordering = ['name']
        indexes = [
            models.Index(fields=['type', 'status']),
            models.Index(fields=['last_verified']),
            models.Index(fields=['name', 'code'])
        ]
        verbose_name = 'Institution'
        verbose_name_plural = 'Institutions'

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

    def clean(self) -> None:
        """
        Enhanced validation with comprehensive data checks.
        """
        try:
            # Validate institution type
            self.type = validate_institution_type(self.type)

            # Validate contact info structure
            required_contact_fields = {'email', 'phone', 'department'}
            if not all(field in self.contact_info for field in required_contact_fields):
                raise ValidationError({
                    'contact_info': f"Missing required fields: {required_contact_fields}"
                })

            # Validate address components
            required_address_fields = {'street', 'city', 'state', 'postal_code'}
            if not all(field in self.address for field in required_address_fields):
                raise ValidationError({
                    'address': f"Missing required fields: {required_address_fields}"
                })

            # Validate accreditation data
            if self.accreditation:
                required_accreditation_fields = {'body', 'status', 'expiration_date'}
                if not all(field in self.accreditation for field in required_accreditation_fields):
                    raise ValidationError({
                        'accreditation': f"Missing required fields: {required_accreditation_fields}"
                    })

        except Exception as e:
            raise ValidationError({
                'validation': f"Institution validation failed: {str(e)}"
            })

    def get_active_courses(self, filters: Optional[Dict] = None) -> models.QuerySet:
        """
        Get all active courses with caching and filtering.
        
        Args:
            filters: Optional filtering criteria
            
        Returns:
            QuerySet: Filtered active courses
        """
        cache_key = f"institution:{self.pk}:courses:{hash(str(filters))}"
        cached_courses = cache.get(cache_key)

        if cached_courses is None:
            courses = self.course_set.filter(is_active=True)
            if filters:
                courses = courses.filter(**filters)
            cache.set(cache_key, courses, timeout=3600)  # Cache for 1 hour
            return courses
        return cached_courses

    def get_transfer_requirements(self, major_code: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get transfer requirements with optional major filtering.
        
        Args:
            major_code: Optional major code filter
            
        Returns:
            List[Dict]: Transfer requirements
        """
        cache_key = f"institution:{self.pk}:requirements:{major_code or 'all'}"
        cached_requirements = cache.get(cache_key)

        if cached_requirements is None:
            requirements = self.transferrequirement_set.filter(is_active=True)
            if major_code:
                requirements = requirements.filter(major_code=major_code)
            requirements_data = list(requirements.values())
            cache.set(cache_key, requirements_data, timeout=1800)  # Cache for 30 minutes
            return requirements_data
        return cached_requirements