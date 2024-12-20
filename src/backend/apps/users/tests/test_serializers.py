"""
Comprehensive test suite for user-related serializers ensuring secure data handling,
validation accuracy, and proper authorization checks.

Version: 1.0
"""

# Django/DRF imports - v4.2+/3.14+
from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError

# Third-party imports
from faker import Faker  # v18.9.0

# Internal imports
from apps.users.serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    PasswordChangeSerializer
)
from apps.users.models import User
from apps.institutions.models import Institution

class TestUserSerializer(TestCase):
    """
    Test cases for UserSerializer ensuring proper validation and security of user data.
    Implements comprehensive validation testing for user profile management.
    """
    
    def setUp(self):
        """Initialize test environment with secure test data."""
        self.faker = Faker()
        self.institution = Institution.objects.create(
            name="Test University",
            code="TEST-U",
            type="university",
            status="active"
        )
        
        # Create valid test data
        self.valid_user_data = {
            'email': self.faker.email(),
            'first_name': self.faker.first_name(),
            'last_name': self.faker.last_name(),
            'role': 'student',
            'institution': self.institution.id,
            'preferences': {
                'notification_settings': {
                    'email_notifications': True,
                    'web_notifications': True
                },
                'display_preferences': {
                    'theme': 'light',
                    'language': 'en'
                }
            },
            'is_active': True
        }
        
        self.serializer = UserSerializer(data=self.valid_user_data)

    def test_valid_user_serialization(self):
        """Verify correct serialization of valid user data."""
        self.assertTrue(self.serializer.is_valid())
        validated_data = self.serializer.validated_data
        
        # Verify all required fields are present
        self.assertEqual(validated_data['email'], self.valid_user_data['email'])
        self.assertEqual(validated_data['first_name'], self.valid_user_data['first_name'])
        self.assertEqual(validated_data['last_name'], self.valid_user_data['last_name'])
        self.assertEqual(validated_data['role'], self.valid_user_data['role'])
        self.assertEqual(validated_data['institution'].id, self.valid_user_data['institution'])

    def test_email_validation(self):
        """Test comprehensive email validation rules."""
        invalid_emails = [
            'invalid@email',  # Missing TLD
            '@domain.com',    # Missing local part
            'spaces in@email.com',  # Contains spaces
            'unicode@ドメイン.com',  # Unicode domain
            'email@.com',     # Missing domain
            'email@domain.',  # Incomplete TLD
            'email@-domain.com',  # Invalid domain start
            'email@domain..com'   # Consecutive dots
        ]
        
        for invalid_email in invalid_emails:
            data = self.valid_user_data.copy()
            data['email'] = invalid_email
            serializer = UserSerializer(data=data)
            
            with self.assertRaises(ValidationError) as context:
                serializer.is_valid(raise_exception=True)
            self.assertIn('email', context.exception.detail)

    def test_role_based_validation(self):
        """Validate role-based access control and institution requirements."""
        role_institution_cases = [
            ('admin', None),  # Admin doesn't require institution
            ('institution_admin', self.institution.id),  # Requires institution
            ('counselor', self.institution.id),  # Requires institution
            ('student', self.institution.id),  # Requires institution
            ('guest', None)  # Guest doesn't require institution
        ]
        
        for role, institution_id in role_institution_cases:
            data = self.valid_user_data.copy()
            data['role'] = role
            data['institution'] = institution_id
            
            serializer = UserSerializer(data=data)
            if role in ['institution_admin', 'counselor', 'student'] and not institution_id:
                with self.assertRaises(ValidationError) as context:
                    serializer.is_valid(raise_exception=True)
                self.assertIn('institution', context.exception.detail)
            else:
                self.assertTrue(serializer.is_valid())

    def test_preferences_validation(self):
        """Test validation of user preferences structure."""
        invalid_preferences = [
            {},  # Empty preferences
            {'notification_settings': {}},  # Missing display_preferences
            {'display_preferences': {}},  # Missing notification_settings
            {'invalid_key': {}}  # Invalid preference key
        ]
        
        for invalid_pref in invalid_preferences:
            data = self.valid_user_data.copy()
            data['preferences'] = invalid_pref
            serializer = UserSerializer(data=data)
            
            with self.assertRaises(ValidationError) as context:
                serializer.is_valid(raise_exception=True)
            self.assertIn('preferences', str(context.exception.detail))

class TestUserRegistrationSerializer(TestCase):
    """
    Test cases for secure user registration process.
    Implements comprehensive validation for user creation.
    """
    
    def setUp(self):
        """Set up test environment for registration testing."""
        self.faker = Faker()
        self.institution = Institution.objects.create(
            name="Test University",
            code="TEST-U",
            type="university",
            status="active"
        )
        
        # Create valid registration data
        self.valid_registration_data = {
            'email': self.faker.email(),
            'password': 'SecurePass123!@#',
            'confirm_password': 'SecurePass123!@#',
            'first_name': self.faker.first_name(),
            'last_name': self.faker.last_name(),
            'role': 'student',
            'institution': self.institution.id
        }

    def test_password_security(self):
        """Validate password security requirements."""
        weak_passwords = [
            'short',           # Too short
            'nodigits',       # No numbers
            'no-uppercase',   # No uppercase
            'NO-LOWERCASE',   # No lowercase
            'NoSpecial1',     # No special characters
            'Common123!',     # Common password
            '12345678!@#',    # No letters
        ]
        
        for weak_password in weak_passwords:
            data = self.valid_registration_data.copy()
            data['password'] = weak_password
            data['confirm_password'] = weak_password
            
            serializer = UserRegistrationSerializer(data=data)
            with self.assertRaises(ValidationError) as context:
                serializer.is_valid(raise_exception=True)
            self.assertIn('password', str(context.exception.detail))

    def test_password_confirmation(self):
        """Verify password confirmation validation."""
        data = self.valid_registration_data.copy()
        data['confirm_password'] = 'DifferentPass123!@#'
        
        serializer = UserRegistrationSerializer(data=data)
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn('password', context.exception.detail)

    def test_duplicate_email_prevention(self):
        """Verify prevention of duplicate email registration."""
        # Create initial user
        User.objects.create_user(
            email=self.valid_registration_data['email'],
            password='InitialPass123!@#'
        )
        
        # Attempt duplicate registration
        serializer = UserRegistrationSerializer(data=self.valid_registration_data)
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn('email', context.exception.detail)

class TestPasswordChangeSerializer(TestCase):
    """
    Test cases for secure password change functionality.
    Implements comprehensive validation for password updates.
    """
    
    def setUp(self):
        """Set up password change test environment."""
        self.current_password = 'CurrentPass123!@#'
        self.user = User.objects.create_user(
            email=self.faker.email(),
            password=self.current_password
        )
        
        self.valid_password_data = {
            'old_password': self.current_password,
            'new_password': 'NewSecurePass456!@#',
            'confirm_password': 'NewSecurePass456!@#'
        }
        
        # Mock request context
        self.context = {'request': type('Request', (), {'user': self.user})}

    def test_old_password_validation(self):
        """Verify current password validation."""
        data = self.valid_password_data.copy()
        data['old_password'] = 'WrongPass123!@#'
        
        serializer = PasswordChangeSerializer(
            context=self.context,
            data=data
        )
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn('old_password', context.exception.detail)

    def test_password_reuse_prevention(self):
        """Verify prevention of password reuse."""
        data = self.valid_password_data.copy()
        data['new_password'] = self.current_password
        data['confirm_password'] = self.current_password
        
        serializer = PasswordChangeSerializer(
            context=self.context,
            data=data
        )
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn('new_password', context.exception.detail)