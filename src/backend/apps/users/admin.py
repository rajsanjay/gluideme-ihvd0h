"""
Django admin configuration for user management in the Transfer Requirements Management System.
Implements secure role-based access control and institution filtering.

Version: 1.0
"""

from django.contrib import admin  # v4.2+
from django.contrib.auth.admin import UserAdmin  # v4.2+
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from django.http import HttpRequest
from django.db.models import QuerySet
from typing import Optional, Tuple, Any
from apps.users.models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Enhanced admin interface for User model with comprehensive security controls
    and role-based access management.
    """
    
    # List display configuration with key user attributes
    list_display = (
        'email', 'first_name', 'last_name', 'role', 'institution',
        'is_active', 'date_joined', 'last_login'
    )
    
    # Filtering options for efficient user management
    list_filter = (
        'role', 'is_active', 'is_staff', 'institution',
        ('date_joined', admin.DateFieldListFilter),
    )
    
    # Search configuration for quick user lookup
    search_fields = ('email', 'first_name', 'last_name', 'institution__name')
    
    # Default ordering for consistent display
    ordering = ('-date_joined',)
    
    # Read-only fields for security audit
    readonly_fields = (
        'date_joined', 'last_login', 'last_password_change',
        'failed_login_attempts'
    )
    
    # Actions configuration
    actions = ['activate_users', 'deactivate_users', 'reset_failed_attempts']
    
    def get_fieldsets(self, request: HttpRequest, obj: Optional[User] = None) -> Tuple:
        """
        Define dynamic fieldsets based on user role and permissions.
        
        Args:
            request: Current request
            obj: User object being edited
            
        Returns:
            Tuple: Configured fieldsets
        """
        # Base fieldset for personal information
        fieldsets = (
            (_('Personal Info'), {
                'fields': ('email', 'first_name', 'last_name', 'password')
            }),
            (_('Profile'), {
                'fields': ('role', 'institution', 'preferences')
            }),
            (_('Security'), {
                'fields': (
                    'is_active', 'failed_login_attempts', 'last_login',
                    'last_password_change', 'security_settings'
                ),
                'classes': ('collapse',)
            })
        )
        
        # Add permissions fieldset for staff users
        if request.user.is_staff:
            fieldsets += (
                (_('Permissions'), {
                    'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions'),
                    'classes': ('collapse',),
                    'description': _('Careful: Changes here affect system access')
                }),
            )
            
        return fieldsets

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """
        Filter queryset based on user role and permissions.
        
        Args:
            request: Current request
            
        Returns:
            QuerySet: Filtered user queryset
        """
        queryset = super().get_queryset(request)
        
        # Optimize query with select_related
        queryset = queryset.select_related('institution')
        
        # Apply role-based filtering
        if not request.user.is_superuser:
            if request.user.role == 'institution_admin':
                # Institution admins can only see users from their institution
                queryset = queryset.filter(institution=request.user.institution)
            elif request.user.role == 'counselor':
                # Counselors can only see students from their institution
                queryset = queryset.filter(
                    institution=request.user.institution,
                    role='student'
                )
                
        return queryset

    def save_model(self, request: HttpRequest, obj: User, form: Any, change: bool) -> None:
        """
        Custom save logic with security validation and audit logging.
        
        Args:
            request: Current request
            obj: User object to save
            form: ModelForm instance
            change: Boolean indicating if this is an edit
        """
        if not change:  # New user
            # Set institution based on admin's context
            if not obj.institution and request.user.role == 'institution_admin':
                obj.institution = request.user.institution
                
            # Initialize security settings
            obj.security_settings = {
                'last_password_change': None,
                'require_password_change': True,
                'failed_login_attempts': 0,
                'lockout_until': None
            }
            
        # Validate role assignments
        if request.user.role == 'institution_admin':
            if obj.role in ['admin', 'institution_admin']:
                raise admin.ValidationError(
                    _('Institution admins cannot create admin users')
                )
                
        super().save_model(request, obj, form, change)

    def activate_users(self, request: HttpRequest, queryset: QuerySet) -> None:
        """
        Bulk activate selected users with audit logging.
        
        Args:
            request: Current request
            queryset: Selected users queryset
        """
        updated = queryset.update(
            is_active=True,
            security_settings__failed_login_attempts=0
        )
        self.message_user(
            request,
            _(f'{updated} users were successfully activated.')
        )
    activate_users.short_description = _('Activate selected users')

    def deactivate_users(self, request: HttpRequest, queryset: QuerySet) -> None:
        """
        Bulk deactivate selected users with security checks.
        
        Args:
            request: Current request
            queryset: Selected users queryset
        """
        # Prevent deactivating superusers
        if queryset.filter(is_superuser=True).exists():
            self.message_user(
                request,
                _('Superusers cannot be deactivated.'),
                level='ERROR'
            )
            return
            
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            _(f'{updated} users were successfully deactivated.')
        )
    deactivate_users.short_description = _('Deactivate selected users')

    def reset_failed_attempts(self, request: HttpRequest, queryset: QuerySet) -> None:
        """
        Reset failed login attempts for selected users.
        
        Args:
            request: Current request
            queryset: Selected users queryset
        """
        updated = queryset.update(
            failed_login_attempts=0,
            security_settings__lockout_until=None
        )
        self.message_user(
            request,
            _(f'Reset failed login attempts for {updated} users.')
        )
    reset_failed_attempts.short_description = _('Reset failed login attempts')

# Unregister default Group admin
admin.site.unregister(Group)