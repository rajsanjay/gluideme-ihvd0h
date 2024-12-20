"""
Unit tests for User model and UserManager in the Transfer Requirements Management System.
Tests user creation, authentication, role-based access control, and data security.

Version: 1.0
"""

import pytest  # v7.0+
from freezegun import freeze_time  # v1.2+
from django.core.exceptions import ValidationError
from apps.users.models import User, ROLE_CHOICES
from datetime import datetime, timezone
import uuid

# Test constants
TEST_PASSWORD = "testpass123"
TEST_EMAIL = "test@example.com"

def create_test_user(data=None):
    """
    Helper function to create test users with default values.
    
    Args:
        data (dict): Override default user data
        
    Returns:
        User: Created test user instance
    """
    default_data = {
        'email': f"test_{uuid.uuid4().hex[:8]}@example.com",
        'password': TEST_PASSWORD,
        'first_name': 'Test',
        'last_name': 'User',
        'role': 'student'
    }
    if data:
        default_data.update(data)
    return User.objects.create_user(**default_data)

@pytest.mark.django_db
class TestUserManager:
    """Test cases for UserManager functionality."""

    def test_create_user(self):
        """Test regular user creation with validation."""
        user = User.objects.create_user(
            email=TEST_EMAIL,
            password=TEST_PASSWORD,
            first_name='Test',
            last_name='User',
            role='student'
        )

        assert user.email == TEST_EMAIL
        assert user.check_password(TEST_PASSWORD)
        assert not user.is_staff
        assert not user.is_superuser
        assert user.role == 'student'
        assert user.is_active
        assert user.security_settings['failed_login_attempts'] == 0
        assert user.security_settings['require_password_change'] is False
        assert 'last_password_change' in user.security_settings

    def test_create_user_invalid_email(self):
        """Test user creation with invalid email format."""
        with pytest.raises(ValidationError) as exc:
            User.objects.create_user(
                email='invalid_email',
                password=TEST_PASSWORD
            )
        assert 'email' in str(exc.value)

    def test_create_user_no_email(self):
        """Test user creation without email."""
        with pytest.raises(ValidationError) as exc:
            User.objects.create_user(
                email='',
                password=TEST_PASSWORD
            )
        assert 'Email address is required' in str(exc.value)

    def test_create_user_invalid_role(self):
        """Test user creation with invalid role."""
        with pytest.raises(ValidationError) as exc:
            User.objects.create_user(
                email=TEST_EMAIL,
                password=TEST_PASSWORD,
                role='invalid_role'
            )
        assert 'Invalid role specified' in str(exc.value)

    def test_create_superuser(self):
        """Test superuser creation with admin privileges."""
        admin = User.objects.create_superuser(
            email=TEST_EMAIL,
            password=TEST_PASSWORD,
            first_name='Admin',
            last_name='User'
        )

        assert admin.email == TEST_EMAIL
        assert admin.check_password(TEST_PASSWORD)
        assert admin.is_staff
        assert admin.is_superuser
        assert admin.role == 'admin'
        assert admin.is_active

    def test_create_superuser_not_staff(self):
        """Test superuser creation with is_staff=False."""
        with pytest.raises(ValidationError) as exc:
            User.objects.create_superuser(
                email=TEST_EMAIL,
                password=TEST_PASSWORD,
                is_staff=False
            )
        assert 'Superuser must have is_staff=True' in str(exc.value)

    def test_create_superuser_not_superuser(self):
        """Test superuser creation with is_superuser=False."""
        with pytest.raises(ValidationError) as exc:
            User.objects.create_superuser(
                email=TEST_EMAIL,
                password=TEST_PASSWORD,
                is_superuser=False
            )
        assert 'Superuser must have is_superuser=True' in str(exc.value)

@pytest.mark.django_db
class TestUser:
    """Test cases for User model functionality."""

    def test_get_full_name(self):
        """Test full name generation with proper formatting."""
        user = create_test_user({
            'first_name': 'John',
            'last_name': 'Doe'
        })
        assert user.get_full_name() == 'John Doe'

    def test_get_short_name(self):
        """Test short name retrieval."""
        user = create_test_user({
            'first_name': 'John',
            'last_name': 'Doe'
        })
        assert user.get_short_name() == 'John'

    def test_has_institution_access_admin(self):
        """Test institution access for admin role."""
        admin = create_test_user({
            'role': 'admin'
        })
        random_institution_id = uuid.uuid4()
        assert admin.has_institution_access(random_institution_id)

    def test_has_institution_access_institution_admin(self):
        """Test institution access for institution admin role."""
        institution_id = uuid.uuid4()
        inst_admin = create_test_user({
            'role': 'institution_admin',
            'institution_id': institution_id
        })
        
        assert inst_admin.has_institution_access(institution_id)
        assert not inst_admin.has_institution_access(uuid.uuid4())

    def test_has_institution_access_counselor(self):
        """Test institution access for counselor role."""
        institution_id = uuid.uuid4()
        counselor = create_test_user({
            'role': 'counselor',
            'institution_id': institution_id
        })
        
        assert counselor.has_institution_access(institution_id)
        assert not counselor.has_institution_access(uuid.uuid4())

    def test_has_institution_access_student(self):
        """Test institution access for student role."""
        institution_id = uuid.uuid4()
        student = create_test_user({
            'role': 'student',
            'institution_id': institution_id
        })
        
        assert student.has_institution_access(institution_id)
        assert not student.has_institution_access(uuid.uuid4())

    def test_has_institution_access_guest(self):
        """Test institution access for guest role."""
        guest = create_test_user({
            'role': 'guest'
        })
        assert not guest.has_institution_access(uuid.uuid4())

    def test_user_preferences(self):
        """Test user preferences JSON field operations."""
        user = create_test_user()
        
        # Test setting preferences
        preferences = {
            'theme': 'dark',
            'notifications': {
                'email': True,
                'push': False
            }
        }
        user.preferences = preferences
        user.save()
        
        # Refresh from database
        user.refresh_from_db()
        assert user.preferences == preferences
        assert user.preferences['theme'] == 'dark'
        assert user.preferences['notifications']['email'] is True

    @freeze_time("2023-01-01 12:00:00")
    def test_security_settings(self):
        """Test security settings management."""
        user = create_test_user()
        
        # Test initial security settings
        assert user.security_settings['failed_login_attempts'] == 0
        assert user.security_settings['require_password_change'] is False
        assert datetime.fromisoformat(
            user.security_settings['last_password_change']
        ).replace(tzinfo=timezone.utc) == datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc)

    def test_str_representation(self):
        """Test string representation of user."""
        user = create_test_user({
            'first_name': 'John',
            'last_name': 'Doe',
            'email': TEST_EMAIL
        })
        assert str(user) == f"John Doe ({TEST_EMAIL})"

    def test_role_choices(self):
        """Test role choices validation."""
        valid_roles = dict(ROLE_CHOICES).keys()
        for role in valid_roles:
            user = create_test_user({'role': role})
            assert user.role == role