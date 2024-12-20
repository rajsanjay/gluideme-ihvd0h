"""
Django admin configuration for managing courses and course equivalencies.
Implements secure admin interfaces with comprehensive validation, versioning, and audit logging.

Version: 1.0
"""

from django.contrib import admin  # v4.2+
from django.contrib.admin import SimpleListFilter
from django.utils import timezone
from django.http import HttpRequest
from django.core.cache import cache
from django.db.models import Q
from typing import List, Tuple, Any, Optional

from apps.courses.models import Course, CourseEquivalency
from apps.core.admin import BaseModelAdmin, VersionedModelAdmin
from utils.exceptions import ValidationError

class CourseStatusFilter(SimpleListFilter):
    """
    Enhanced custom filter for course status with caching and validation.
    """
    title = 'Status'
    parameter_name = 'status'
    cache_timeout = 300  # 5 minutes cache

    def lookups(self, request: HttpRequest, model_admin: Any) -> List[Tuple[str, str]]:
        """
        Get cached status choices with validation.
        
        Args:
            request: The incoming request
            model_admin: The model admin instance
            
        Returns:
            List of status choice tuples
        """
        cache_key = 'course_status_filter_choices'
        choices = cache.get(cache_key)

        if choices is None:
            choices = [
                ('active', 'Active'),
                ('inactive', 'Inactive'),
                ('pending', 'Pending Review'),
                ('archived', 'Archived')
            ]
            cache.set(cache_key, choices, self.cache_timeout)

        return choices

    def queryset(self, request: HttpRequest, queryset: Any) -> Any:
        """
        Filter queryset with security validation.
        
        Args:
            request: The incoming request
            queryset: Base queryset to filter
            
        Returns:
            Filtered queryset
        """
        if not self.value():
            return queryset

        try:
            # Apply security filters based on user role
            if not request.user.is_superuser:
                queryset = queryset.filter(
                    Q(institution__in=request.user.get_accessible_institutions()) |
                    Q(status='active')
                )

            return queryset.filter(status=self.value())

        except Exception as e:
            raise ValidationError(
                message="Status filter error",
                validation_errors={'status': str(e)}
            )

@admin.register(Course)
class CourseAdmin(VersionedModelAdmin):
    """
    Enhanced admin interface for Course model with versioning and security.
    """
    list_display = [
        'code', 'name', 'institution', 'credits', 'status',
        'valid_from', 'valid_to', 'version'
    ]
    list_filter = [
        CourseStatusFilter,
        'institution',
        'valid_from',
        'valid_to'
    ]
    search_fields = [
        'code',
        'name',
        'institution__name'
    ]
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'version',
        'last_validated'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'institution', 'description', 'credits')
        }),
        ('Status & Validity', {
            'fields': ('status', 'valid_from', 'valid_to')
        }),
        ('Prerequisites', {
            'fields': ('prerequisites',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('System Fields', {
            'fields': readonly_fields,
            'classes': ('collapse',)
        })
    )
    filter_horizontal = ('prerequisites',)

    def save_model(self, request: HttpRequest, obj: Course, 
                  form: Any, change: bool) -> None:
        """
        Enhanced save with validation and version control.
        
        Args:
            request: The incoming request
            obj: Course instance to save
            form: The form instance
            change: Whether this is a change operation
        """
        try:
            # Validate course data
            obj.full_clean()

            # Check status transition
            if change and 'status' in form.changed_data:
                obj.validate_status_transition(form.initial['status'], obj.status)

            # Create new version if needed
            if change and form.changed_data:
                version_data = {
                    'version': obj.version + 1,
                    'timestamp': timezone.now().isoformat(),
                    'change_reason': request.POST.get('change_reason', 'Administrative update'),
                    'changed_fields': form.changed_data,
                    'modified_by': request.user.email
                }
                obj.version_metadata['version_history'] = obj.version_metadata.get('version_history', [])
                obj.version_metadata['version_history'].append(version_data)

            # Update audit information
            obj.metadata.update({
                'last_modified_by': request.user.email,
                'modified_at': timezone.now().isoformat(),
                'ip_address': request.META.get('REMOTE_ADDR')
            })

            super().save_model(request, obj, form, change)

            # Invalidate relevant caches
            cache.delete_pattern(f"course:*:{obj.pk}")

        except ValidationError as e:
            self.message_user(request, str(e), level='ERROR')
            raise

@admin.register(CourseEquivalency)
class CourseEquivalencyAdmin(BaseModelAdmin):
    """
    Enhanced admin interface for CourseEquivalency with validation.
    """
    list_display = [
        'source_course',
        'target_course',
        'effective_date',
        'expiration_date',
        'validation_status'
    ]
    list_filter = [
        'source_course__institution',
        'target_course__institution',
        'effective_date',
        'expiration_date',
        'validation_status'
    ]
    search_fields = [
        'source_course__code',
        'target_course__code',
        'notes'
    ]
    raw_id_fields = ['source_course', 'target_course']
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'last_reviewed'
    ]
    fieldsets = (
        ('Course Mapping', {
            'fields': ('source_course', 'target_course')
        }),
        ('Validity Period', {
            'fields': ('effective_date', 'expiration_date')
        }),
        ('Status', {
            'fields': ('validation_status', 'notes')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('System Fields', {
            'fields': readonly_fields,
            'classes': ('collapse',)
        })
    )

    def save_model(self, request: HttpRequest, obj: CourseEquivalency, 
                  form: Any, change: bool) -> None:
        """
        Enhanced save with validation and audit logging.
        
        Args:
            request: The incoming request
            obj: CourseEquivalency instance to save
            form: The form instance
            change: Whether this is a change operation
        """
        try:
            # Validate equivalency data
            obj.full_clean()

            # Validate date ranges
            if obj.expiration_date:
                obj.validate_date_range(obj.effective_date, obj.expiration_date)

            # Check for circular references
            self._validate_circular_references(obj)

            # Update review information
            obj.reviewed_by = request.user
            obj.last_reviewed = timezone.now()

            # Update audit information
            obj.metadata.update({
                'last_modified_by': request.user.email,
                'modified_at': timezone.now().isoformat(),
                'ip_address': request.META.get('REMOTE_ADDR')
            })

            super().save_model(request, obj, form, change)

            # Invalidate relevant caches
            cache.delete_pattern(f"equivalency:*:{obj.pk}")

        except ValidationError as e:
            self.message_user(request, str(e), level='ERROR')
            raise

    def _validate_circular_references(self, obj: CourseEquivalency) -> None:
        """
        Validate that no circular references exist in course equivalencies.
        
        Args:
            obj: CourseEquivalency instance to validate
            
        Raises:
            ValidationError: If circular reference is detected
        """
        visited = set()
        
        def check_cycle(course, path):
            if course.id in path:
                raise ValidationError({
                    'equivalency': f"Circular reference detected: {' -> '.join(path)}"
                })
            path.add(course.id)
            
            # Check forward equivalencies
            for equiv in course.source_equivalencies.all():
                check_cycle(equiv.target_course, path.copy())
                
            # Check backward equivalencies
            for equiv in course.target_equivalencies.all():
                check_cycle(equiv.source_course, path.copy())

        check_cycle(obj.source_course, set())