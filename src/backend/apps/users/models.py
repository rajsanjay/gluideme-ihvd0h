"""
Django models for user management in the Transfer Requirements Management System.
Implements secure user authentication, role-based access control, and enhanced security features.

Version: 1.0
"""

from django.db import models  # v4.2+
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin  # v4.2+
from django.contrib.auth.hashers import make_password  # v4.2+
from django.utils import timezone
from apps.core.models import BaseModel
from utils.exceptions import ValidationError
from typing import Dict, Any, Optional
import uuid

# Role choices with granular access levels
ROLE_CHOICES = (
    ('admin', 'Administrator'),
    ('institution_admin', 'Institution Administrator'),
    ('counselor', 'Academic Counselor'),
    ('student', 'Student'),
    ('guest', 'Guest')
)

class UserManager(BaseUserManager):
    """
    Enhanced custom user manager with comprehensive security validation.
    Implements secure user creation and management functionality.
    """
    
    def create_user(self, email: str, password: str = None, **extra_fields) -> 'User':
        """
        Create and save a user with enhanced security validation.
        
        Args:
            email: User's email address
            password: User's password
            **extra_fields: Additional user fields
            
        Returns:
            User: Created user instance
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            if not email:
                raise ValidationError(
                    message="Email address is required",
                    validation_errors={'email': 'This field is required'}
                )
                
            # Normalize and validate email
            email = self.normalize_email(email)
            
            # Validate role if provided
            role = extra_fields.get('role', 'guest')
            if role not in dict(ROLE_CHOICES):
                raise ValidationError(
                    message="Invalid role specified",
                    validation_errors={'role': f"Must be one of: {', '.join(dict(ROLE_CHOICES).keys())}"}
                )
                
            # Create user instance
            user = self.model(
                email=email,
                **extra_fields
            )
            
            # Set password with secure hashing
            user.password = make_password(password)
            
            # Initialize security settings
            user.security_settings = {
                'last_password_change': timezone.now().isoformat(),
                'require_password_change': False,
                'failed_login_attempts': 0,
                'lockout_until': None
            }
            
            user.save(using=self._db)
            return user
            
        except Exception as e:
            raise ValidationError(
                message="Failed to create user",
                validation_errors={'user': str(e)}
            )

    def create_superuser(self, email: str, password: str = None, **extra_fields) -> 'User':
        """
        Create and save a superuser with maximum security measures.
        
        Args:
            email: Admin email address
            password: Admin password
            **extra_fields: Additional admin fields
            
        Returns:
            User: Created superuser instance
            
        Raises:
            ValidationError: If validation fails
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValidationError(
                message="Superuser must have is_staff=True",
                validation_errors={'is_staff': 'Must be True for superuser'}
            )
            
        if extra_fields.get('is_superuser') is not True:
            raise ValidationError(
                message="Superuser must have is_superuser=True",
                validation_errors={'is_superuser': 'Must be True for superuser'}
            )
            
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    """
    Enhanced custom user model with comprehensive security features.
    Implements secure authentication, role-based access, and audit logging.
    """
    
    # Core user fields with enhanced validation
    email = models.EmailField(
        unique=True,
        db_index=True,
        help_text="User's email address for authentication"
    )
    first_name = models.CharField(
        max_length=150,
        help_text="User's first name"
    )
    last_name = models.CharField(
        max_length=150,
        help_text="User's last name"
    )
    
    # Role and access control
    role = models.CharField(
        max_length=50,
        choices=ROLE_CHOICES,
        db_index=True,
        help_text="User's role for access control"
    )
    institution = models.ForeignKey(
        'institutions.Institution',
        null=True,
        on_delete=models.SET_NULL,
        db_index=True,
        help_text="Associated institution for role-based access"
    )
    
    # Status flags
    is_active = models.BooleanField(
        default=True,
        help_text="User account status"
    )
    is_staff = models.BooleanField(
        default=False,
        help_text="Staff access status"
    )
    
    # Timestamps
    date_joined = models.DateTimeField(
        auto_now_add=True,
        help_text="Account creation timestamp"
    )
    last_login = models.DateTimeField(
        null=True,
        help_text="Last successful login timestamp"
    )
    
    # User preferences and security settings
    preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text="User preferences and settings"
    )
    security_settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="Security configurations and status"
    )
    last_password_change = models.DateTimeField(
        null=True,
        help_text="Last password change timestamp"
    )
    failed_login_attempts = models.IntegerField(
        default=0,
        help_text="Count of failed login attempts"
    )
    
    # User manager and authentication settings
    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'role']
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email', 'role']),
            models.Index(fields=['institution', 'role']),
            models.Index(fields=['last_login', 'is_active'])
        ]
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self) -> str:
        return f"{self.get_full_name()} ({self.email})"
    
    def get_full_name(self) -> str:
        """
        Get user's full name with proper formatting.
        
        Returns:
            str: Formatted full name
        """
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self) -> str:
        """
        Get user's first name with validation.
        
        Returns:
            str: Validated first name
        """
        return self.first_name.strip()
    
    def has_institution_access(self, institution_id: uuid.UUID) -> bool:
        """
        Verify user's access rights for a specific institution.
        
        Args:
            institution_id: UUID of institution to check
            
        Returns:
            bool: Whether user has access
        """
        # Admins have global access
        if self.role == 'admin':
            return True
            
        # Institution admins and counselors must be affiliated
        if self.role in ['institution_admin', 'counselor']:
            return str(self.institution.id) == str(institution_id)
            
        # Students can access their own institution
        if self.role == 'student':
            return str(self.institution.id) == str(institution_id)
            
        # Guests have no institution access
        return False