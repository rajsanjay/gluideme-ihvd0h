"""
Django admin interface configuration for validation models.
Implements comprehensive administrative views for managing validation records
and caches with enhanced audit logging, accuracy metrics, and filtering.

Version: 1.0
"""

from django.contrib import admin  # v4.2+
from django.contrib.admin import SimpleListFilter
from django.http import HttpRequest
from django.utils import timezone
from apps.validation.models import ValidationRecord, ValidationCache
from apps.core.admin import BaseModelAdmin
from typing import List, Tuple, Any, Optional

class ValidationStatusFilter(SimpleListFilter):
    """
    Enhanced custom admin filter for validation status with accuracy metrics.
    Provides filtering by validation status with performance indicators.
    """
    title = 'validation status'
    parameter_name = 'status'

    def lookups(self, request: HttpRequest, model_admin: Any) -> List[Tuple[str, str]]:
        """
        Define enhanced filter options with accuracy metrics.
        
        Args:
            request: The incoming request
            model_admin: The model admin instance
            
        Returns:
            List of status filter tuples with accuracy indicators
        """
        # Get aggregated accuracy metrics for each status
        metrics = ValidationRecord.objects.values('status').annotate(
            avg_accuracy=models.Avg('accuracy_score')
        )
        
        # Format status choices with accuracy indicators
        status_choices = []
        for status in ('pending', 'in_progress', 'valid', 'invalid', 'error'):
            metric = next((m for m in metrics if m['status'] == status), None)
            accuracy = f" (Avg Accuracy: {metric['avg_accuracy']:.2f}%)" if metric else ""
            status_choices.append((status, f"{status.title()}{accuracy}"))
            
        return status_choices

    def queryset(self, request: HttpRequest, queryset: Any) -> Any:
        """
        Optimized filter queryset by status with performance considerations.
        
        Args:
            request: The incoming request
            queryset: Base queryset to filter
            value: Selected filter value
            
        Returns:
            Filtered validation records with optimized joins
        """
        if not self.value():
            return queryset
            
        # Optimize query with select_related
        return queryset.filter(
            status=self.value()
        ).select_related(
            'requirement',
            'course'
        ).prefetch_related(
            'requirement__source_institution',
            'requirement__target_institution'
        )

@admin.register(ValidationRecord)
class ValidationRecordAdmin(BaseModelAdmin):
    """
    Enhanced admin interface for validation records with accuracy monitoring.
    Provides comprehensive validation management with audit logging.
    """
    list_display = [
        'requirement',
        'course',
        'status',
        'accuracy_score',
        'validated_at',
        'valid_until',
        'performance_impact'
    ]
    list_filter = [
        ValidationStatusFilter,
        'validated_at',
        'valid_until',
        'accuracy_score'
    ]
    search_fields = [
        'requirement__id',
        'course__code',
        'metadata__contains'
    ]
    readonly_fields = [
        'validated_at',
        'valid_until',
        'results',
        'metadata',
        'accuracy_metrics',
        'performance_metrics'
    ]
    
    def save_model(self, request: HttpRequest, obj: ValidationRecord, 
                  form: Any, change: bool) -> None:
        """
        Enhanced save with validation and audit logging.
        
        Args:
            request: The incoming request
            obj: ValidationRecord instance
            form: The form instance
            change: Whether this is a change operation
        """
        try:
            # Perform validation for new records
            if not change:
                validation_results = obj.validate()
                obj.results = validation_results
                
            # Calculate accuracy metrics
            if obj.status == 'valid':
                obj.calculate_accuracy()
                
            # Update metadata with audit info
            obj.metadata.update({
                'last_modified_by': request.user.email,
                'modified_at': timezone.now().isoformat(),
                'validation_metrics': {
                    'accuracy_score': obj.accuracy_score,
                    'performance_impact': obj.performance_impact
                }
            })
            
            # Save with parent class
            super().save_model(request, obj, form, change)
            
            # Log validation change
            self.log_change(
                request,
                obj,
                f"Validation {'updated' if change else 'created'} with "
                f"status: {obj.status}, accuracy: {obj.accuracy_score}%"
            )
            
        except Exception as e:
            self.message_user(
                request,
                f"Error saving validation record: {str(e)}",
                level='ERROR'
            )
            raise

@admin.register(ValidationCache)
class ValidationCacheAdmin(BaseModelAdmin):
    """
    Enhanced admin interface for validation cache entries with performance monitoring.
    Provides cache management with performance metrics.
    """
    list_display = [
        'requirement',
        'course',
        'cache_key',
        'hit_rate',
        'created_at',
        'expires_at',
        'performance_score'
    ]
    list_filter = [
        'created_at',
        'expires_at',
        'hit_rate'
    ]
    search_fields = [
        'cache_key',
        'requirement__id',
        'course__code'
    ]
    readonly_fields = [
        'cache_key',
        'created_at',
        'expires_at',
        'results',
        'performance_metrics',
        'hit_rate_metrics'
    ]

    def has_add_permission(self, request: HttpRequest) -> bool:
        """
        Enhanced permission check with security logging.
        Prevents manual cache creation for data integrity.
        
        Args:
            request: The incoming request
            
        Returns:
            False to prevent manual cache creation
        """
        # Log access attempt
        self.log_change(
            request,
            None,
            "Attempted manual cache creation (prevented)"
        )
        
        # Cache entries should only be created programmatically
        return False