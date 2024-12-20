"""
Unit tests for core validation utilities ensuring accurate validation of course codes, 
credits, institution types, and requirement rules.

Version: 1.0
"""

import pytest  # v7.0+
from decimal import Decimal
from utils.validators import (
    validate_course_code,
    validate_credits,
    validate_institution_type,
    validate_requirement_rules
)
from utils.exceptions import ValidationError

def pytest_configure(config):
    """Configure pytest environment for validation tests."""
    # Register custom markers
    config.addinivalue_line(
        "markers", "validation: mark test as validation test"
    )

class TestCourseCodeValidator:
    """Test cases for course code validation function."""
    
    @pytest.mark.parametrize('code,expected', [
        ('CS 101', 'CS 101'),
        ('MATH 1A', 'MATH 1A'),
        ('PHYS 21L', 'PHYS 21L'),
        ('BIO 1A', 'BIO 1A'),
        ('CHEM 101', 'CHEM 101'),
        ('ENG 1B', 'ENG 1B'),
        ('HIST 10', 'HIST 10'),
        ('PSYCH 100', 'PSYCH 100'),
        ('SOC 1', 'SOC 1'),
        ('ECON 1A', 'ECON 1A')
    ])
    def test_valid_course_codes(self, code, expected):
        """Test validation of correctly formatted course codes."""
        result = validate_course_code(code)
        assert result == expected
        assert isinstance(result, str)
        assert ' ' in result  # Verify space separator
        dept, num = result.split()
        assert dept in {'CS', 'MATH', 'PHYS', 'BIO', 'CHEM', 'ENG', 'HIST', 'PSYCH', 'SOC', 'ECON'}

    @pytest.mark.parametrize('invalid_code,error_msg', [
        ('CS', 'Invalid course code format'),
        ('101', 'Invalid department code'),
        ('CS-101', 'Invalid course code format'),
        ('CS101', 'Invalid course code format'),
        ('', 'Course code validation failed'),
        ('CS 1A1', 'Invalid course code format'),
        ('INVALID 101', 'Invalid department code'),
        ('CS 0', 'Invalid course number'),
        ('CS 100000', 'Invalid course number'),
        ('12 345', 'Invalid department code'),
        (None, 'Course code validation failed'),
        ('CS  101', 'Invalid course code format'),  # Double space
        ('cs 101', 'Invalid course code format'),  # Lowercase
        ('CS 101A2', 'Invalid course code format'),  # Invalid suffix
        ('TOOLONG 101', 'Invalid department code')  # Department too long
    ])
    def test_invalid_course_codes(self, invalid_code, error_msg):
        """Test rejection of incorrectly formatted course codes."""
        with pytest.raises(ValidationError) as exc_info:
            validate_course_code(invalid_code)
        assert error_msg in str(exc_info.value)
        assert exc_info.value.error_code.startswith('VAL_')
        assert 'validation_errors' in exc_info.value.error_details

class TestCreditsValidator:
    """Test cases for course credits validation function."""
    
    @pytest.mark.parametrize('credits,expected', [
        (3.0, Decimal('3.00')),
        (4.5, Decimal('4.50')),
        (0.5, Decimal('0.50')),
        (12.0, Decimal('12.00')),
        ('3.25', Decimal('3.25')),
        (Decimal('4.75'), Decimal('4.75')),
        (1.75, Decimal('1.75')),
        (2.25, Decimal('2.25')),
        (5.0, Decimal('5.00')),
        (0.25, Decimal('0.25'))
    ])
    def test_valid_credits(self, credits, expected):
        """Test validation of valid credit values."""
        result = validate_credits(credits)
        assert result == expected
        assert isinstance(result, Decimal)
        assert result % Decimal('0.25') == 0  # Verify 0.25 increment
        assert Decimal('0') < result <= Decimal('12')

    @pytest.mark.parametrize('invalid_credits,error_msg', [
        (-1.0, 'Invalid credit value'),
        (13.0, 'Invalid credit value'),
        ('abc', 'Credit validation failed'),
        (0.0, 'Invalid credit value'),
        (None, 'Credit validation failed'),
        (0.1, 'Invalid credit increment'),
        (12.1, 'Invalid credit value'),
        ('12.123', 'Invalid credit increment'),
        (float('inf'), 'Credit validation failed'),
        (0.33, 'Invalid credit increment'),
        (Decimal('-0.25'), 'Invalid credit value'),
        ('0.255', 'Invalid credit increment')
    ])
    def test_invalid_credits(self, invalid_credits, error_msg):
        """Test rejection of invalid credit values."""
        with pytest.raises(ValidationError) as exc_info:
            validate_credits(invalid_credits)
        assert error_msg in str(exc_info.value)
        assert exc_info.value.error_code.startswith('VAL_')
        assert 'credits' in exc_info.value.error_details.get('validation_errors', {})

class TestInstitutionTypeValidator:
    """Test cases for institution type validation function."""
    
    @pytest.mark.parametrize('type_name,expected', [
        ('university', 'university'),
        ('college', 'college'),
        ('community_college', 'community_college'),
        ('UNIVERSITY', 'university'),
        ('College', 'college'),
        ('COMMUNITY_COLLEGE', 'community_college'),
        (' university ', 'university'),  # Test trimming
        ('  college  ', 'college'),
        ('community_college  ', 'community_college')
    ])
    def test_valid_institution_types(self, type_name, expected):
        """Test validation of valid institution types."""
        result = validate_institution_type(type_name)
        assert result == expected
        assert isinstance(result, str)
        assert result in {'university', 'college', 'community_college'}

    @pytest.mark.parametrize('invalid_type,error_msg', [
        ('school', 'Invalid institution type'),
        ('academy', 'Invalid institution type'),
        ('', 'Invalid institution type'),
        (None, 'Institution type validation failed'),
        ('123', 'Invalid institution type'),
        ('invalid_college', 'Invalid institution type'),
        ('university_college', 'Invalid institution type'),
        ('community-college', 'Invalid institution type'),
        (' ', 'Invalid institution type'),
        ('unknown', 'Invalid institution type')
    ])
    def test_invalid_institution_types(self, invalid_type, error_msg):
        """Test rejection of invalid institution types."""
        with pytest.raises(ValidationError) as exc_info:
            validate_institution_type(invalid_type)
        assert error_msg in str(exc_info.value)
        assert exc_info.value.error_code.startswith('VAL_')
        assert 'institution_type' in exc_info.value.error_details.get('validation_errors', {})

class TestRequirementRulesValidator:
    """Test cases for requirement rules validation function."""

    def test_valid_requirement_rules(self):
        """Test validation of valid requirement rule structures."""
        valid_rules = {
            'courses': [
                {'code': 'CS 101', 'credits': 3.0},
                {'code': 'MATH 1A', 'credits': 4.0}
            ],
            'min_credits': 7.0,
            'prerequisites': {
                'CS 101': [],
                'MATH 1A': ['CS 101']
            }
        }
        
        result = validate_requirement_rules(valid_rules)
        assert isinstance(result, dict)
        assert 'courses' in result
        assert 'min_credits' in result
        assert 'prerequisites' in result
        assert len(result['courses']) == 2
        assert isinstance(result['min_credits'], Decimal)
        assert isinstance(result['prerequisites'], dict)

    def test_invalid_requirement_rules(self):
        """Test rejection of invalid requirement rule structures."""
        invalid_rules = {
            'courses': [
                {'code': 'INVALID', 'credits': -1.0},
                {'code': '101', 'credits': 'abc'}
            ],
            'min_credits': 20.0,
            'prerequisites': {
                'CS101': ['MATH1A'],
                'MATH1A': ['invalid']
            }
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_requirement_rules(invalid_rules)
        assert 'Rule validation failed' in str(exc_info.value)
        assert exc_info.value.error_code.startswith('VAL_')
        assert 'rules' in exc_info.value.error_details.get('validation_errors', {})

    def test_missing_required_keys(self):
        """Test validation fails when required keys are missing."""
        incomplete_rules = {
            'courses': [],
            'min_credits': 3.0
            # missing prerequisites
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_requirement_rules(incomplete_rules)
        assert 'Missing required rule keys' in str(exc_info.value)
        assert 'prerequisites' in exc_info.value.error_details.get('validation_errors', {}).get('rules', '')

    def test_circular_prerequisites(self):
        """Test detection of circular prerequisite dependencies."""
        circular_rules = {
            'courses': [
                {'code': 'CS 101', 'credits': 3.0},
                {'code': 'CS 102', 'credits': 3.0},
                {'code': 'CS 103', 'credits': 3.0}
            ],
            'min_credits': 9.0,
            'prerequisites': {
                'CS 101': ['CS 103'],
                'CS 102': ['CS 101'],
                'CS 103': ['CS 102']
            }
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_requirement_rules(circular_rules)
        assert 'Circular prerequisite dependency detected' in str(exc_info.value)
        assert 'prerequisites' in exc_info.value.error_details.get('validation_errors', {})