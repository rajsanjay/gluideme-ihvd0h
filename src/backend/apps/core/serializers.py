"""
Core serializer classes for the Transfer Requirements Management System.
Implements comprehensive serialization, validation, versioning and audit logging.

Version: 1.0
"""

# Django REST Framework v3.14+
from rest_framework import serializers
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from django.core.cache import cache

# Internal imports
from apps.core.models import BaseModel, VersionedModel
from utils.validators import validate_course_code, validate_credits

class BaseModelSerializer(serializers.ModelSerializer):
    """
    Enhanced base serializer providing comprehensive validation and metadata handling.
    Implements core serialization functionality with optimized caching.
    """
    id = serializers.UUIDField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    is_active = serializers.BooleanField(default=True)
    metadata = serializers.JSONField(required=False, default=dict)

    class Meta:
        model = BaseModel
        fields = ['id', 'created_at', 'updated_at', 'is_active', 'metadata']

    def __init__(self, *args, **kwargs):
        """Initialize serializer with enhanced validation setup."""
        super().__init__(*args, **kwargs)
        self.validation_errors = {}
        self.cache_key_prefix = f"{self.Meta.model.__name__}_"

    def validate(self, data):
        """
        Enhanced validation with comprehensive checks and caching.
        
        Args:
            data (dict): Data to validate
            
        Returns:
            dict: Validated and sanitized data
        """
        try:
            # Validate base fields
            if not data.get('is_active', True):
                data['metadata'] = {
                    **data.get('metadata', {}),
                    'deactivated_at': timezone.now().isoformat()
                }

            # Validate metadata format
            if metadata := data.get('metadata'):
                if not isinstance(metadata, dict):
                    raise ValidationError({
                        'metadata': 'Metadata must be a valid JSON object'
                    })
                
                # Sanitize metadata
                sanitized_metadata = self._sanitize_metadata(metadata)
                data['metadata'] = sanitized_metadata

            return super().validate(data)

        except ValidationError as e:
            self.validation_errors.update(e.detail)
            raise

    def _sanitize_metadata(self, metadata):
        """
        Sanitize metadata to remove sensitive information.
        
        Args:
            metadata (dict): Raw metadata
            
        Returns:
            dict: Sanitized metadata
        """
        sensitive_keys = {'password', 'token', 'secret', 'key', 'credential'}
        sanitized = {}
        
        for key, value in metadata.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                continue
            sanitized[key] = value
            
        return sanitized

    def bulk_create(self, data_list):
        """
        Optimized bulk creation with validation and caching.
        
        Args:
            data_list (list): List of data dictionaries
            
        Returns:
            list: Created model instances
        """
        # Validate all records
        validated_data_list = []
        for data in data_list:
            validated_data = self.validate(data)
            validated_data_list.append(validated_data)

        # Perform bulk creation
        instances = self.Meta.model.objects.bulk_create([
            self.Meta.model(**data) for data in validated_data_list
        ])

        # Update cache for each instance
        for instance in instances:
            cache_key = f"{self.cache_key_prefix}{instance.id}"
            cache.set(cache_key, instance, timeout=3600)  # 1 hour cache

        return instances

class VersionedModelSerializer(BaseModelSerializer):
    """
    Enhanced serializer mixin for comprehensive version control.
    Implements temporal versioning with effective dating and chain validation.
    """
    version = serializers.IntegerField(read_only=True)
    effective_from = serializers.DateTimeField(required=False)
    effective_to = serializers.DateTimeField(read_only=True)
    previous_version = serializers.UUIDField(read_only=True)
    version_metadata = serializers.JSONField(required=False, default=dict)

    class Meta:
        model = VersionedModel
        fields = BaseModelSerializer.Meta.fields + [
            'version', 'effective_from', 'effective_to', 
            'previous_version', 'version_metadata'
        ]

    def create_version(self, validated_data):
        """
        Create new version with comprehensive tracking.
        
        Args:
            validated_data (dict): Validated data for new version
            
        Returns:
            VersionedModel: New version instance
        """
        try:
            # Validate version chain
            current_instance = self.instance
            if current_instance and current_instance.effective_to:
                raise ValidationError({
                    'version': 'Cannot create new version from expired record'
                })

            # Set effective dates
            effective_from = validated_data.pop('effective_from', timezone.now())
            
            # Create version metadata
            version_metadata = {
                'created_from': str(current_instance.id) if current_instance else None,
                'changed_fields': list(validated_data.keys()),
                'change_timestamp': timezone.now().isoformat()
            }

            # Create new version
            new_version = current_instance.create_new_version(
                data=validated_data,
                reason=validated_data.get('change_reason', ''),
                effective_date=effective_from
            )

            # Update cache
            cache_key = f"{self.cache_key_prefix}{new_version.id}"
            cache.set(cache_key, new_version, timeout=3600)

            return new_version

        except Exception as e:
            raise ValidationError({
                'version': f'Failed to create new version: {str(e)}'
            })

    def validate_version_transition(self, data):
        """
        Validate version transition rules.
        
        Args:
            data (dict): Data for version transition
            
        Returns:
            bool: Validation result
        """
        if not self.instance:
            return True

        # Validate temporal constraints
        effective_from = data.get('effective_from', timezone.now())
        if effective_from <= self.instance.effective_from:
            raise ValidationError({
                'effective_from': 'New version must be effective after current version'
            })

        # Validate version chain
        if not self.instance.validate_version_chain():
            raise ValidationError({
                'version': 'Version chain validation failed'
            })

        return True

class AuditModelSerializer(BaseModelSerializer):
    """
    Serializer mixin for comprehensive audit logging.
    Implements detailed change tracking with user attribution.
    """
    created_by = serializers.UUIDField(required=False)
    updated_by = serializers.UUIDField(read_only=True)
    change_log = serializers.JSONField(read_only=True)
    change_type = serializers.ChoiceField(
        choices=['create', 'update', 'delete', 'restore'],
        required=False
    )
    audit_metadata = serializers.JSONField(required=False, default=dict)

    def validate(self, data):
        """
        Validate audit fields with enhanced security.
        
        Args:
            data (dict): Data to validate
            
        Returns:
            dict: Validated data
        """
        data = super().validate(data)

        # Validate user references
        if 'created_by' in data and not data['created_by']:
            raise ValidationError({
                'created_by': 'User reference is required'
            })

        # Validate audit metadata
        if audit_metadata := data.get('audit_metadata'):
            if not isinstance(audit_metadata, dict):
                raise ValidationError({
                    'audit_metadata': 'Audit metadata must be a valid JSON object'
                })

        return data

    def log_change(self, changes, change_type):
        """
        Log changes with detailed tracking.
        
        Args:
            changes (dict): Changed field values
            change_type (str): Type of change
            
        Returns:
            dict: Audit log entry
        """
        try:
            # Format change entry
            change_entry = {
                'timestamp': timezone.now().isoformat(),
                'change_type': change_type,
                'user_id': str(self.context['request'].user.id),
                'changes': changes,
                'metadata': {
                    'ip_address': self.context['request'].META.get('REMOTE_ADDR'),
                    'user_agent': self.context['request'].META.get('HTTP_USER_AGENT')
                }
            }

            # Update instance change log
            if not isinstance(self.instance.change_log, list):
                self.instance.change_log = []
            self.instance.change_log.append(change_entry)
            
            # Update audit fields
            self.instance.updated_by = self.context['request'].user.id
            self.instance.save(update_fields=['change_log', 'updated_by', 'updated_at'])

            return change_entry

        except Exception as e:
            raise ValidationError({
                'audit': f'Failed to log change: {str(e)}'
            })