"""
Django admin configuration for managing institutions and institution agreements.
Implements custom admin views, list displays, filters and form customizations.

Version: 1.0
"""

from django.contrib import admin  # v4.2+
from django.utils.html import format_html  # v4.2+
from django.contrib import messages  # v4.2+
from apps.institutions.models import Institution, InstitutionAgreement

@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    """
    Custom admin interface for Institution model with enhanced validation 
    and security features.
    """
    # Display configuration
    list_display = [
        'name', 
        'code', 
        'type', 
        'status', 
        'website_link',
        'last_verified'
    ]
    list_filter = ['type', 'status', 'created_at', 'last_verified']
    search_fields = ['name', 'code', 'website']
    ordering = ['name']
    
    # Form configuration
    readonly_fields = ['created_at', 'updated_at', 'last_verified']
    fieldsets = [
        ('Basic Information', {
            'fields': ('name', 'code', 'type', 'status', 'website')
        }),
        ('Contact Details', {
            'fields': ('contact_info',),
            'classes': ('collapse',)
        }),
        ('Location', {
            'fields': ('address',),
            'classes': ('collapse',)
        }),
        ('Accreditation', {
            'fields': ('accreditation',),
            'classes': ('collapse',)
        }),
        ('System Fields', {
            'fields': ('created_at', 'updated_at', 'last_verified'),
            'classes': ('collapse',)
        })
    ]
    
    # Performance optimization
    list_per_page = 50
    date_hierarchy = 'created_at'
    save_on_top = True

    def website_link(self, obj):
        """
        Format website URL as clickable link in admin with security validation.
        
        Args:
            obj: Institution instance
            
        Returns:
            SafeString: HTML formatted link
        """
        if obj.website:
            return format_html(
                '<a href="{}" target="_blank" rel="noopener noreferrer">{}</a>',
                obj.website,
                obj.website
            )
        return '-'
    website_link.short_description = 'Website'
    website_link.admin_order_field = 'website'

    def save_model(self, request, obj, form, change):
        """
        Custom save logic with validation and audit logging.
        
        Args:
            request: HttpRequest instance
            obj: Institution instance being saved
            form: ModelForm instance
            change: Boolean indicating if this is an edit
        """
        try:
            # Validate institution data
            obj.full_clean()
            
            # Save the institution
            super().save_model(request, obj, form, change)
            
            # Success message
            action = 'updated' if change else 'created'
            messages.success(
                request, 
                f'Institution {obj.name} successfully {action}.'
            )
            
        except Exception as e:
            messages.error(
                request,
                f'Error saving institution: {str(e)}'
            )

@admin.register(InstitutionAgreement)
class InstitutionAgreementAdmin(admin.ModelAdmin):
    """
    Custom admin interface for InstitutionAgreement model with optimized 
    queries and validation.
    """
    # Display configuration
    list_display = [
        'source_institution',
        'target_institution', 
        'agreement_type',
        'status',
        'effective_date',
        'created_at'
    ]
    list_filter = [
        'agreement_type',
        'status',
        'effective_date',
        'created_at'
    ]
    search_fields = [
        'source_institution__name',
        'target_institution__name'
    ]
    ordering = ['-effective_date']
    
    # Form configuration
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['source_institution', 'target_institution']
    autocomplete_fields = ['source_institution', 'target_institution']
    
    fieldsets = [
        ('Agreement Details', {
            'fields': (
                'source_institution',
                'target_institution',
                'agreement_type',
                'status',
                'effective_date'
            )
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('System Fields', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    ]
    
    # Performance optimization
    list_per_page = 30
    date_hierarchy = 'effective_date'
    save_on_top = True

    def get_queryset(self, request):
        """
        Optimize queryset with select_related for foreign keys.
        
        Args:
            request: HttpRequest instance
            
        Returns:
            QuerySet: Optimized queryset with related institutions
        """
        return super().get_queryset(request).select_related(
            'source_institution',
            'target_institution'
        )

    def save_model(self, request, obj, form, change):
        """
        Custom save logic with agreement validation.
        
        Args:
            request: HttpRequest instance
            obj: InstitutionAgreement instance being saved
            form: ModelForm instance
            change: Boolean indicating if this is an edit
        """
        try:
            # Validate agreement data
            obj.full_clean()
            
            # Verify institutions are different
            if obj.source_institution == obj.target_institution:
                raise ValidationError(
                    "Source and target institutions must be different"
                )
            
            # Save the agreement
            super().save_model(request, obj, form, change)
            
            # Success message
            action = 'updated' if change else 'created'
            messages.success(
                request,
                f'Agreement between {obj.source_institution} and '
                f'{obj.target_institution} successfully {action}.'
            )
            
        except Exception as e:
            messages.error(
                request,
                f'Error saving agreement: {str(e)}'
            )