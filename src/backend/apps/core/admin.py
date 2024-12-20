"""
Django admin configuration for core app models with enhanced security and audit logging.
Implements custom admin views and forms with comprehensive security features.

Version: 1.0
"""

from django.contrib import admin  # v4.2+
from django.contrib.admin import SimpleListFilter
from django.utils import timezone
from django.http import HttpRequest
from django.core.cache import cache
from django.conf import settings
from typing import Any, Dict, Optional, Tuple

from apps.core.models import BaseModel, VersionedModel, AuditModel
from utils.permissions import IsAdmin
from utils.exceptions import PermissionDeniedError

# Admin site customization
admin.site.site_title = "Transfer Requirements Management System"
admin.site.site_header = "TRMS Administration"
admin.site.index_title = "Administration Portal"

# Security settings
ADMIN_SESSION_TIMEOUT = getattr(settings, 'ADMIN_SESSION_TIMEOUT', 3600)  # 1 hour
ADMIN_IP_WHITELIST = getattr(settings, 'ADMIN_IP_WHITELIST', [
    '10.0.0.0/8',     # Private network
    '172.16.0.0/12',  # Private network
    '192.168.0.0/16'  # Private network
])

class SecurityMixin:
    """
    Mixin providing enhanced security features for admin views.
    Implements IP validation, session management, and audit logging.
    """

    def has_module_permission(self, request: HttpRequest) -> bool:
        """
        Enhanced permission check with IP validation and session timeout.
        
        Args:
            request: The incoming request
            
        Returns:
            bool: Whether permission is granted
        """
        try:
            # Validate IP whitelist
            client_ip = request.META.get('REMOTE_ADDR')
            if not any(ip in ADMIN_IP_WHITELIST for ip in [client_ip]):
                raise PermissionDeniedError(
                    message="IP address not whitelisted",
                    required_role="admin"
                )

            # Check session timeout
            last_activity = request.session.get('last_activity')
            if last_activity and (timezone.now().timestamp() - float(last_activity)) > ADMIN_SESSION_TIMEOUT:
                request.session.flush()
                raise PermissionDeniedError(
                    message="Session expired",
                    required_role="admin"
                )

            # Update last activity
            request.session['last_activity'] = timezone.now().timestamp()

            return super().has_module_permission(request)

        except Exception as e:
            self.message_user(request, str(e), level='ERROR')
            return False

class AuditLogFilter(SimpleListFilter):
    """
    Custom filter for audit log entries with enhanced filtering capabilities.
    """
    title = 'audit period'
    parameter_name = 'audit_period'

    def lookups(self, request: HttpRequest, model_admin: Any) -> Tuple[Tuple[str, str], ...]:
        """Define filter options."""
        return (
            ('1h', 'Last Hour'),
            ('24h', 'Last 24 Hours'),
            ('7d', 'Last 7 Days'),
            ('30d', 'Last 30 Days'),
        )

    def queryset(self, request: HttpRequest, queryset: Any) -> Any:
        """Apply the selected filter."""
        if self.value() is None:
            return queryset

        now = timezone.now()
        if self.value() == '1h':
            return queryset.filter(updated_at__gte=now - timezone.timedelta(hours=1))
        elif self.value() == '24h':
            return queryset.filter(updated_at__gte=now - timezone.timedelta(days=1))
        elif self.value() == '7d':
            return queryset.filter(updated_at__gte=now - timezone.timedelta(days=7))
        elif self.value() == '30d':
            return queryset.filter(updated_at__gte=now - timezone.timedelta(days=30))

@admin.register(BaseModel)
class BaseModelAdmin(admin.ModelAdmin, SecurityMixin):
    """
    Enhanced base admin class with advanced security and audit features.
    """
    list_display = ['id', 'created_at', 'updated_at', 'is_active', 'get_last_modified_by', 'get_ip_address']
    list_filter = ['is_active', AuditLogFilter]
    readonly_fields = ['id', 'created_at', 'updated_at', 'get_last_modified_by', 'get_ip_address']
    search_fields = ['id', 'metadata']
    ordering = ['-updated_at']

    def get_last_modified_by(self, obj: BaseModel) -> str:
        """Get user who last modified the record."""
        return obj.metadata.get('last_modified_by', 'Unknown')
    get_last_modified_by.short_description = 'Modified By'

    def get_ip_address(self, obj: BaseModel) -> str:
        """Get IP address of last modification."""
        return obj.metadata.get('ip_address', 'Unknown')
    get_ip_address.short_description = 'IP Address'

    def save_model(self, request: HttpRequest, obj: BaseModel, form: Any, change: bool) -> None:
        """
        Enhanced save with comprehensive audit logging.
        
        Args:
            request: The incoming request
            obj: Model instance to save
            form: The form instance
            change: Whether this is a change operation
        """
        try:
            # Update metadata with audit information
            obj.metadata.update({
                'last_modified_by': request.user.email,
                'ip_address': request.META.get('REMOTE_ADDR'),
                'user_agent': request.META.get('HTTP_USER_AGENT'),
                'modified_at': timezone.now().isoformat()
            })

            # Log the change
            change_message = {
                'action': 'update' if change else 'create',
                'fields': list(form.changed_data),
                'timestamp': timezone.now().isoformat()
            }
            
            if not isinstance(obj.metadata.get('change_history'), list):
                obj.metadata['change_history'] = []
            obj.metadata['change_history'].append(change_message)

            super().save_model(request, obj, form, change)

            # Invalidate relevant caches
            cache_key = f"admin:model:{obj._meta.model_name}:{obj.pk}"
            cache.delete(cache_key)

        except Exception as e:
            self.message_user(request, f"Error saving model: {str(e)}", level='ERROR')
            raise

@admin.register(VersionedModel)
class VersionedModelAdmin(BaseModelAdmin):
    """
    Enhanced admin class for models with comprehensive version control.
    """
    list_display = BaseModelAdmin.list_display + ['version', 'effective_from', 'effective_to']
    list_filter = BaseModelAdmin.list_filter + ['version', 'effective_from', 'effective_to']
    readonly_fields = BaseModelAdmin.readonly_fields + ['version', 'previous_version', 'get_version_history']
    
    def get_version_history(self, obj: VersionedModel) -> str:
        """Format version history for display."""
        history = obj.version_metadata.get('version_history', [])
        return '\n'.join([
            f"Version {item['version']}: {item['change_reason']} ({item['timestamp']})"
            for item in history
        ])
    get_version_history.short_description = 'Version History'

    def save_model(self, request: HttpRequest, obj: VersionedModel, form: Any, change: bool) -> None:
        """
        Enhanced save with comprehensive version control.
        
        Args:
            request: The incoming request
            obj: Model instance to save
            form: The form instance
            change: Whether this is a change operation
        """
        try:
            if change and form.changed_data:
                # Create new version
                version_data = {
                    'version': obj.version + 1,
                    'timestamp': timezone.now().isoformat(),
                    'change_reason': request.POST.get('change_reason', 'Administrative update'),
                    'changed_fields': form.changed_data,
                    'modified_by': request.user.email
                }

                if not isinstance(obj.version_metadata.get('version_history'), list):
                    obj.version_metadata['version_history'] = []
                obj.version_metadata['version_history'].append(version_data)

            super().save_model(request, obj, form, change)

        except Exception as e:
            self.message_user(request, f"Error saving version: {str(e)}", level='ERROR')
            raise