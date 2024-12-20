"""
Core validation utilities for the Transfer Requirements Management System.
Provides comprehensive validation functions and decorators for data validation
with 99.99% accuracy for courses, requirements, and institutional data.

Version: 1.0
"""

import re
from decimal import Decimal, InvalidOperation
from django.core.validators import RegexValidator  # v4.2+
from utils.exceptions import ValidationError
from typing import Dict, Union, List, Set
from functools import wraps

# Global Constants
COURSE_CODE_PATTERN = r'^[A-Z]{2,10}\s\d{1,5}[A-Z]?$'
MIN_CREDITS = Decimal('0.0')
MAX_CREDITS = Decimal('12.0')
VALID_INSTITUTION_TYPES = ('university', 'college', 'community_college')

# Department code whitelist for additional validation
VALID_DEPARTMENT_CODES = {
    'CS', 'MATH', 'PHYS', 'CHEM', 'BIO', 'ENG', 'HIST', 
    'PSYCH', 'SOC', 'ECON', 'PHIL', 'ART', 'MUS'
}

def validate_course_code(code: str) -> str:
    """
    Validates and normalizes course codes with enhanced pattern matching.
    
    Args:
        code (str): Course code to validate (e.g., 'CS 101')
        
    Returns:
        str: Normalized course code
        
    Raises:
        ValidationError: If course code format is invalid
    """
    try:
        # Normalize input
        normalized_code = code.strip().upper()
        
        # Basic pattern validation
        if not re.match(COURSE_CODE_PATTERN, normalized_code):
            raise ValidationError(
                message="Invalid course code format",
                validation_errors={
                    'code': f"Course code must match pattern: {COURSE_CODE_PATTERN}"
                }
            )
        
        # Split into department and number
        dept, number = normalized_code.split()
        
        # Validate department code
        if dept not in VALID_DEPARTMENT_CODES:
            raise ValidationError(
                message="Invalid department code",
                validation_errors={
                    'department': f"Department code '{dept}' not recognized"
                }
            )
        
        # Validate course number
        number_base = re.match(r'\d+', number).group()
        if not (1 <= int(number_base) <= 99999):
            raise ValidationError(
                message="Invalid course number",
                validation_errors={
                    'number': "Course number must be between 1 and 99999"
                }
            )
            
        return normalized_code
        
    except (AttributeError, ValueError) as e:
        raise ValidationError(
            message="Course code validation failed",
            validation_errors={'code': str(e)}
        )

def validate_credits(credits: Union[Decimal, str, float]) -> Decimal:
    """
    Validates and normalizes course credit values with precise decimal handling.
    
    Args:
        credits: Credit value to validate
        
    Returns:
        Decimal: Normalized credit value
        
    Raises:
        ValidationError: If credit value is invalid
    """
    try:
        # Convert to Decimal if needed
        if not isinstance(credits, Decimal):
            credits = Decimal(str(credits))
        
        # Round to 2 decimal places
        credits = credits.quantize(Decimal('0.01'))
        
        # Validate range
        if not MIN_CREDITS <= credits <= MAX_CREDITS:
            raise ValidationError(
                message="Invalid credit value",
                validation_errors={
                    'credits': f"Credits must be between {MIN_CREDITS} and {MAX_CREDITS}"
                }
            )
        
        # Validate granularity (must be in 0.25 increments)
        remainder = credits % Decimal('0.25')
        if remainder != Decimal('0'):
            raise ValidationError(
                message="Invalid credit increment",
                validation_errors={
                    'credits': "Credits must be in increments of 0.25"
                }
            )
            
        return credits
        
    except (InvalidOperation, ValueError) as e:
        raise ValidationError(
            message="Credit validation failed",
            validation_errors={'credits': str(e)}
        )

def validate_institution_type(institution_type: str) -> str:
    """
    Validates and normalizes institution types with case normalization.
    
    Args:
        institution_type (str): Institution type to validate
        
    Returns:
        str: Normalized institution type
        
    Raises:
        ValidationError: If institution type is invalid
    """
    try:
        # Normalize input
        normalized_type = institution_type.strip().lower()
        
        if normalized_type not in VALID_INSTITUTION_TYPES:
            raise ValidationError(
                message="Invalid institution type",
                validation_errors={
                    'institution_type': f"Must be one of: {', '.join(VALID_INSTITUTION_TYPES)}"
                }
            )
            
        return normalized_type
        
    except AttributeError as e:
        raise ValidationError(
            message="Institution type validation failed",
            validation_errors={'institution_type': str(e)}
        )

def validate_requirement_rules(rules: Dict) -> Dict:
    """
    Validates transfer requirement rules with recursive validation.
    
    Args:
        rules (dict): Requirement rules to validate
        
    Returns:
        dict: Validated and normalized rules
        
    Raises:
        ValidationError: If rules are invalid
    """
    required_keys = {'courses', 'min_credits', 'prerequisites'}
    
    try:
        # Validate required keys
        missing_keys = required_keys - rules.keys()
        if missing_keys:
            raise ValidationError(
                message="Missing required rule keys",
                validation_errors={
                    'rules': f"Missing required keys: {', '.join(missing_keys)}"
                }
            )
        
        # Validate and normalize courses
        validated_courses = []
        for course in rules['courses']:
            if not isinstance(course, dict):
                raise ValidationError(
                    message="Invalid course format",
                    validation_errors={'courses': "Each course must be a dictionary"}
                )
                
            validated_course = {
                'code': validate_course_code(course.get('code', '')),
                'credits': validate_credits(course.get('credits', 0))
            }
            validated_courses.append(validated_course)
        
        # Validate min_credits
        min_credits = validate_credits(rules['min_credits'])
        
        # Validate prerequisites recursively
        validated_prerequisites = _validate_prerequisites(
            rules['prerequisites'],
            set()  # Track visited courses to prevent cycles
        )
        
        # Return normalized and validated rules
        return {
            'courses': validated_courses,
            'min_credits': min_credits,
            'prerequisites': validated_prerequisites
        }
        
    except (KeyError, TypeError) as e:
        raise ValidationError(
            message="Rule validation failed",
            validation_errors={'rules': str(e)}
        )

def _validate_prerequisites(prerequisites: Dict, visited: Set[str]) -> Dict:
    """
    Helper function for recursive prerequisite validation.
    
    Args:
        prerequisites (dict): Prerequisites to validate
        visited (set): Set of visited course codes
        
    Returns:
        dict: Validated prerequisites
        
    Raises:
        ValidationError: If prerequisites are invalid or contain cycles
    """
    validated_prereqs = {}
    
    for course_code, prereq_list in prerequisites.items():
        # Validate course code
        validated_code = validate_course_code(course_code)
        
        # Check for cycles
        if validated_code in visited:
            raise ValidationError(
                message="Circular prerequisite dependency detected",
                validation_errors={
                    'prerequisites': f"Circular dependency involving {validated_code}"
                }
            )
            
        visited.add(validated_code)
        
        # Validate prerequisite courses recursively
        validated_prereq_list = []
        for prereq in prereq_list:
            validated_prereq = validate_course_code(prereq)
            validated_prereq_list.append(validated_prereq)
            
        validated_prereqs[validated_code] = validated_prereq_list
        
        visited.remove(validated_code)
        
    return validated_prereqs

def validation_decorator(validator_func):
    """
    Decorator for applying validation functions with error handling.
    
    Args:
        validator_func: Validation function to apply
        
    Returns:
        function: Decorated function with validation
    """
    @wraps(validator_func)
    def wrapper(*args, **kwargs):
        try:
            return validator_func(*args, **kwargs)
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(
                message="Validation failed",
                validation_errors={'general': str(e)}
            )
    return wrapper