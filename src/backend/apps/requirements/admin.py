"""
Django admin configuration for managing transfer requirements with enhanced security,
version control, and comprehensive audit logging.

Version: 1.0
"""

from django.contrib import admin  # v4.2+
from django.contrib.admin import SimpleListFilter
from django.utils.html import format_html
from django.core.cache import cache
from django.utils import timezone
from django.http import HttpRequest

from apps.requirements.models import TransferRequirement, RequirementCourse
from apps.core.admin import VersionedModelAdmin
from utils.permissions import IsAdmin
from typing import Any, Dict, List, Optional, Tuple

# Cache timeout for admin filters
FILTER_CACHE_TTL = 300  # 5 minutes

class RequirementStatusFilter(SimpleListFilter):
    """
    Enhanced filter for requirement status with caching and security validation.
    """
    title = 'Status'
    parameter_name = 'status'

    def lookups(self, request: HttpRequest, model_admin: Any) -> List[Tuple[str, str]]:
        """
        Get cached status options with security validation.
        """
        cache_key = f"admin:requirement_status_filter:{request.user.id}"
        cached_lookups = cache.get(cache_key)

        if cached_lookups is not None:
            return cached_lookups

        lookups = [
            ('active', 'Active'),
            ('pending', 'Pending Review'),
            ('expired', 'Expired'),
            ('archived', 'Archived')
        ]

        cache.set(cache_key, lookups, timeout=FILTER_CACHE_TTL)
        return lookups

    def queryset(self, request: HttpRequest, queryset: Any) -> Any:
        """
        Filter queryset with security scoping and caching.
        """
        if not self.value():
            return queryset

        cache_key = f"admin:requirement_filter:{request.user.id}:{self.value()}"
        cached_qs = cache.get(cache_key)

        if cached_qs is not None:
            return cached_qs

        now = timezone.now()
        
        if self.value() == 'active':
            qs = queryset.filter(
                status='published',
                effective_date__lte=now,
                expiration_date__gt=now
            )
        elif self.value() == 'pending':
            qs = queryset.filter(status='draft')
        elif self.value() == 'expired':
            qs = queryset.filter(expiration_date__lte=now)
        elif self.value() == 'archived':
            qs = queryset.filter(status='archived')
        else:
            qs = queryset

        cache.set(cache_key, qs, timeout=FILTER_CACHE_TTL)
        return qs

@admin.register(TransferRequirement)
class TransferRequirementAdmin(VersionedModelAdmin):
    """
    Enhanced admin interface for transfer requirements with comprehensive security,
    version control, and audit logging.
    """
    list_display = [
        'title',
        'source_institution',
        'target_institution',
        'major_code',
        'type',
        'status_with_icon',
        'effective_date',
        'version',
        'validation_accuracy'
    ]
    list_filter = [
        RequirementStatusFilter,
        'type',
        'source_institution',
        'target_institution',
        ('effective_date', admin.DateFieldListFilter)
    ]
    search_fields = [
        'title',
        'major_code',
        'description',
        'metadata'
    ]
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'version',
        'validation_accuracy',
        'last_modified_by',
        'audit_log'
    ]
    
    fieldsets = [
        ('Basic Information', {
            'fields': (
                'title',
                'major_code',
                'description',
                'type'
            )
        }),
        ('Institutions', {
            'fields': (
                'source_institution',
                'target_institution'
            )
        }),
        ('Requirements', {
            'fields': (
                'rules',
                'metadata'
            )
        }),
        ('Validity', {
            'fields': (
                'status',
                'effective_date',
                'expiration_date',
                'validation_accuracy'
            )
        }),
        ('Audit Information', {
            'classes': ('collapse',),
            'fields': (
                'version',
                'created_at',
                'updated_at',
                'last_modified_by',
                'audit_log'
            )
        })
    ]

    def status_with_icon(self, obj: TransferRequirement) -> str:
        """
        Display status with color-coded icon.
        """
        icons = {
            'published': '🟢',
            'draft': '🟡',
            'archived': '⚫'
        }
        return format_html(
            '{} {}',
            icons.get(obj.status, '⚪'),
            obj.get_status_display()
        )
    status_with_icon.short_description = 'Status'

    def save_model(self, request: HttpRequest, obj: TransferRequirement, 
                  form: Any, change: bool) -> None:
        """
        Enhanced save with version control and audit logging.
        """
        try:
            # Validate requirement data
            obj.validate_requirement()

            # Update metadata
            if not change:
                obj.metadata['created_by'] = request.user.email
            obj.metadata['last_modified_by'] = request.user.email
            obj.metadata['last_modified_at'] = timezone.now().isoformat()

            # Create new version if changed
            if change and form.changed_data:
                obj.version += 1
                obj.version_metadata['change_reason'] = request.POST.get(
                    'change_reason',
                    'Administrative update'
                )
                obj.version_metadata['changed_fields'] = form.changed_data

            # Save the model
            super().save_model(request, obj, form, change)

            # Clear related caches
            cache.delete_pattern(f"requirement:*:{obj.pk}")
            cache.delete_pattern(f"admin:requirement_filter:*")

        except Exception as e:
            self.message_user(
                request,
                f"Error saving requirement: {str(e)}",
                level='ERROR'
            )
            raise

    def get_queryset(self, request: HttpRequest) -> Any:
        """
        Get queryset with security scoping and annotations.
        """
        qs = super().get_queryset(request)

        # Apply role-based filtering
        if not request.user.is_superuser:
            if request.user.role == 'institution_admin':
                qs = qs.filter(
                    source_institution=request.user.institution
                )

        # Add annotations
        qs = qs.select_related(
            'source_institution',
            'target_institution'
        ).prefetch_related(
            'metadata',
            'version_metadata'
        )

        return qs

    class Media:
        css = {
            'all': ('admin/css/requirements.css',)
        }
        js = ('admin/js/requirements.js',)

@admin.register(RequirementCourse)
class RequirementCourseAdmin(VersionedModelAdmin):
    """
    Admin interface for requirement course mappings with validation.
    """
    list_display = [
        'requirement',
        'course',
        'status',
        'validation_status',
        'last_validated'
    ]
    list_filter = [
        'status',
        'validation_status',
        'requirement__source_institution'
    ]
    search_fields = [
        'requirement__title',
        'course__code'
    ]
    readonly_fields = [
        'validation_status',
        'last_validated'
    ]

    def save_model(self, request: HttpRequest, obj: RequirementCourse, 
                  form: Any, change: bool) -> None:
        """
        Save with validation checks.
        """
        try:
            # Validate course mapping
            obj.validate_equivalency()
            obj.check_institution_compatibility()
            super().save_model(request, obj, form, change)
        except Exception as e:
            self.message_user(
                request,
                f"Error saving course mapping: {str(e)}",
                level='ERROR'
            )
            raise