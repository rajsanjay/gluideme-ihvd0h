"""
Package initializer for the users Django app implementing secure user management,
authentication, and role-based access control functionality.

This module exposes core user management components and configures the default
Django app settings for the users application.

Version: 1.0
"""

# Import the User model for direct access from apps.users
from apps.users.models import User

# Import role choices for access control
from apps.users.models import ROLE_CHOICES

# Configure default app for Django discovery
default_app_config = 'apps.users.apps.UsersConfig'

# Export commonly used components
__all__ = [
    'User',
    'ROLE_CHOICES',
    'default_app_config',
]

# Define version for package management
__version__ = '1.0'

# Define author for package metadata
__author__ = 'Transfer Requirements Management System'

"""
Role-Based Access Control Matrix:

Admin:
- Full system access
- User management
- System configuration
- All data access

Institution Admin:
- Institution-specific data
- Course management
- Transfer requirement management
- Staff user management

Counselor:
- View/edit student data
- View transfer requirements
- Generate reports
- Student communication

Student:
- View own data
- View transfer requirements
- Plan courses
- Track progress

Guest:
- View public transfer requirements
- Search courses
- No data modification
"""