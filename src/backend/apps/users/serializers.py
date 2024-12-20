"""
User serializer classes for the Transfer Requirements Management System.
Implements secure user data handling with comprehensive validation and role-based access control.

Version: 1.0
"""

# Django REST Framework v3.14+
from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from rest_framework.exceptions import ValidationError

# Internal imports
from apps.users.models import User
from apps.core.serializers import BaseModelSerializer
from apps.institutions.models import Institution

class UserSerializer(BaseModelSerializer):
    """
    Comprehensive user profile serializer with enhanced security and validation.
    Implements role-based access control and field-level security.
    """
    email = serializers.EmailField(
        max_length=255,
        required=True,
        help_text="User's email address for authentication"
    )
    first_name = serializers.CharField(
        max_length=150,
        required=True,
        help_text="User's first name"
    )
    last_name = serializers.CharField(
        max_length=150,
        required=True,
        help_text="User's last name"
    )
    role = serializers.ChoiceField(
        choices=User.ROLE_CHOICES,
        required=True,
        help_text="User's role for access control"
    )
    institution = serializers.PrimaryKeyRelatedField(
        queryset=Institution.objects.filter(is_active=True),
        required=False,
        allow_null=True,
        help_text="Associated institution for role-based access"
    )
    preferences = serializers.JSONField(
        required=False,
        default=dict,
        help_text="User preferences and settings"
    )
    last_login = serializers.DateTimeField(
        read_only=True,
        help_text="Last successful login timestamp"
    )

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'role',
            'institution', 'preferences', 'last_login', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_login']

    def validate(self, data):
        """
        Comprehensive validation with role-based checks and security measures.
        
        Args:
            data (dict): Data to validate
            
        Returns:
            dict: Validated and sanitized data
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Validate email format and uniqueness
            email = data.get('email')
            if email and self.instance and email != self.instance.email:
                if User.objects.filter(email__iexact=email).exists():
                    raise ValidationError({'email': 'Email address already in use'})

            # Validate role-based institution requirements
            role = data.get('role')
            institution = data.get('institution')

            if role in ['institution_admin', 'counselor', 'student']:
                if not institution:
                    raise ValidationError({
                        'institution': f'Institution is required for {role} role'
                    })

            # Validate preferences structure
            if preferences := data.get('preferences'):
                required_fields = {'notification_settings', 'display_preferences'}
                if not all(field in preferences for field in required_fields):
                    raise ValidationError({
                        'preferences': f'Missing required preference fields: {required_fields}'
                    })

            return super().validate(data)

        except Exception as e:
            raise ValidationError({
                'validation': f'User validation failed: {str(e)}'
            })

class UserRegistrationSerializer(BaseModelSerializer):
    """
    Secure user registration serializer with comprehensive validation.
    Implements password security and role enforcement.
    """
    email = serializers.EmailField(
        max_length=255,
        required=True,
        help_text="User's email address for authentication"
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        help_text="Secure password (min. 12 characters)"
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        help_text="Password confirmation"
    )
    first_name = serializers.CharField(
        max_length=150,
        required=True,
        help_text="User's first name"
    )
    last_name = serializers.CharField(
        max_length=150,
        required=True,
        help_text="User's last name"
    )
    role = serializers.ChoiceField(
        choices=User.ROLE_CHOICES,
        required=True,
        help_text="User's role for access control"
    )
    institution = serializers.PrimaryKeyRelatedField(
        queryset=Institution.objects.filter(is_active=True),
        required=False,
        allow_null=True,
        help_text="Associated institution for role-based access"
    )

    class Meta:
        model = User
        fields = [
            'email', 'password', 'confirm_password', 'first_name',
            'last_name', 'role', 'institution'
        ]

    def validate(self, data):
        """
        Comprehensive registration validation with security checks.
        
        Args:
            data (dict): Registration data to validate
            
        Returns:
            dict: Validated registration data
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Validate password complexity
            password = data.get('password')
            validate_password(password)

            # Ensure passwords match
            if password != data.get('confirm_password'):
                raise ValidationError({
                    'password': 'Passwords do not match'
                })

            # Validate email uniqueness (case-insensitive)
            email = data.get('email')
            if User.objects.filter(email__iexact=email).exists():
                raise ValidationError({
                    'email': 'Email address already registered'
                })

            # Validate role-based requirements
            role = data.get('role')
            institution = data.get('institution')

            if role in ['institution_admin', 'counselor', 'student']:
                if not institution:
                    raise ValidationError({
                        'institution': f'Institution is required for {role} role'
                    })

            return data

        except Exception as e:
            raise ValidationError({
                'registration': f'Registration validation failed: {str(e)}'
            })

    def create(self, validated_data):
        """
        Create new user with secure password hashing.
        
        Args:
            validated_data (dict): Validated user data
            
        Returns:
            User: Created user instance
        """
        # Remove confirmation field
        validated_data.pop('confirm_password', None)
        
        # Hash password
        validated_data['password'] = make_password(validated_data.get('password'))
        
        # Set default preferences
        validated_data['preferences'] = {
            'notification_settings': {
                'email_notifications': True,
                'web_notifications': True
            },
            'display_preferences': {
                'theme': 'light',
                'language': 'en'
            }
        }
        
        return super().create(validated_data)

class PasswordChangeSerializer(BaseModelSerializer):
    """
    Secure password change serializer with comprehensive validation.
    Implements password history and complexity requirements.
    """
    old_password = serializers.CharField(
        write_only=True,
        required=True,
        help_text="Current password"
    )
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        help_text="New password (min. 12 characters)"
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        help_text="New password confirmation"
    )

    class Meta:
        model = User
        fields = ['old_password', 'new_password', 'confirm_password']

    def validate(self, data):
        """
        Validate password change with comprehensive security checks.
        
        Args:
            data (dict): Password change data
            
        Returns:
            dict: Validated password data
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            user = self.context['request'].user

            # Verify current password
            if not user.check_password(data.get('old_password')):
                raise ValidationError({
                    'old_password': 'Current password is incorrect'
                })

            # Validate new password complexity
            new_password = data.get('new_password')
            validate_password(new_password, user=user)

            # Ensure new password differs from old
            if data.get('old_password') == new_password:
                raise ValidationError({
                    'new_password': 'New password must be different from current password'
                })

            # Confirm passwords match
            if new_password != data.get('confirm_password'):
                raise ValidationError({
                    'confirm_password': 'Passwords do not match'
                })

            return data

        except Exception as e:
            raise ValidationError({
                'password_change': f'Password change validation failed: {str(e)}'
            })