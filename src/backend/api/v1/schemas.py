"""
Pydantic schema models for validating API request/response data in the Transfer Requirements Management System.
Implements comprehensive validation rules with enhanced security and real-time validation capabilities.

Version: 1.0
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Union
from uuid import UUID
from pydantic import BaseModel, Field, validator, root_validator, EmailStr, SecretStr, Json
from apps.institutions.models import INSTITUTION_TYPES
from apps.courses.models import COURSE_STATUS, METADATA_SCHEMA

# Constants for validation
MIN_NAME_LENGTH = 2
MAX_NAME_LENGTH = 200
MIN_CREDITS = Decimal('0.0')
MAX_CREDITS = Decimal('12.0')
CREDIT_INCREMENT = Decimal('0.25')

class BaseInstitutionSchema(BaseModel):
    """
    Enhanced base schema for institution data validation with security features.
    """
    id: Optional[UUID] = Field(None, description="Institution UUID")
    name: str = Field(
        ..., 
        min_length=MIN_NAME_LENGTH,
        max_length=MAX_NAME_LENGTH,
        description="Official institution name"
    )
    type: str = Field(..., description="Institution type")
    contact_info: Dict = Field(
        default_factory=dict,
        description="Structured contact information"
    )
    active: bool = Field(default=True, description="Institution active status")
    security_classification: Dict = Field(
        default_factory=dict,
        description="Security classification metadata"
    )

    @validator('name')
    def validate_name(cls, value: str) -> str:
        """Validates institution name format with enhanced security."""
        # Strip whitespace and normalize
        value = value.strip()

        # Check length constraints
        if not MIN_NAME_LENGTH <= len(value) <= MAX_NAME_LENGTH:
            raise ValueError(
                f"Name must be between {MIN_NAME_LENGTH} and {MAX_NAME_LENGTH} characters"
            )

        # Check for restricted characters
        restricted_chars = '<>&"\''
        if any(char in value for char in restricted_chars):
            raise ValueError("Name contains invalid characters")

        # Validate against SQL injection patterns
        sql_patterns = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', '--']
        if any(pattern.lower() in value.lower() for pattern in sql_patterns):
            raise ValueError("Name contains restricted patterns")

        return value

    @validator('type')
    def validate_type(cls, value: str) -> str:
        """Validates institution type against allowed values."""
        value = value.lower().strip()
        if value not in [t[0] for t in INSTITUTION_TYPES]:
            raise ValueError(f"Invalid institution type. Must be one of: {[t[0] for t in INSTITUTION_TYPES]}")
        return value

    @validator('contact_info')
    def validate_contact_info(cls, value: Dict) -> Dict:
        """Validates contact information structure and content."""
        required_fields = {'email', 'phone', 'department'}
        missing_fields = required_fields - set(value.keys())
        if missing_fields:
            raise ValueError(f"Missing required contact fields: {missing_fields}")

        # Validate email format
        if 'email' in value:
            EmailStr.validate(value['email'])

        # Validate phone format
        if 'phone' in value:
            phone = str(value['phone']).strip()
            if not phone.replace('-', '').replace('+', '').isdigit():
                raise ValueError("Invalid phone number format")

        return value

    @root_validator
    def validate_security(cls, values: Dict) -> Dict:
        """Validates security-related fields and classifications."""
        if 'security_classification' in values:
            classification = values['security_classification']
            required_security_fields = {'level', 'handling_instructions'}
            if not all(field in classification for field in required_security_fields):
                raise ValueError("Missing required security classification fields")
        return values

class BaseCourseSchema(BaseModel):
    """
    Enhanced base schema for course data validation with temporal support.
    """
    id: Optional[UUID] = Field(None, description="Course UUID")
    code: str = Field(..., description="Course code")
    name: str = Field(
        ...,
        min_length=MIN_NAME_LENGTH,
        max_length=MAX_NAME_LENGTH,
        description="Course name"
    )
    credits: Decimal = Field(..., description="Course credit units")
    metadata: Dict = Field(default_factory=dict, description="Course metadata")
    valid_from: datetime = Field(..., description="Validity start date")
    valid_to: Optional[datetime] = Field(None, description="Validity end date")
    status: str = Field(default='active', description="Course status")

    @validator('code')
    def validate_code(cls, value: str) -> str:
        """Validates course code with institution-specific patterns."""
        value = value.strip().upper()
        
        # Basic format validation
        if not value or len(value) > 20:
            raise ValueError("Invalid course code length")

        # Pattern validation (e.g., "CS 101")
        import re
        if not re.match(r'^[A-Z]{2,10}\s\d{1,5}[A-Z]?$', value):
            raise ValueError("Course code must match pattern (e.g., 'CS 101')")

        return value

    @validator('credits')
    def validate_credits(cls, value: Decimal) -> Decimal:
        """Validates course credit value."""
        if not MIN_CREDITS <= value <= MAX_CREDITS:
            raise ValueError(f"Credits must be between {MIN_CREDITS} and {MAX_CREDITS}")

        # Validate credit increments
        remainder = value % CREDIT_INCREMENT
        if remainder != Decimal('0'):
            raise ValueError(f"Credits must be in increments of {CREDIT_INCREMENT}")

        return value

    @validator('status')
    def validate_status(cls, value: str) -> str:
        """Validates course status."""
        value = value.lower().strip()
        valid_statuses = [status[0] for status in COURSE_STATUS]
        if value not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
        return value

    @validator('metadata')
    def validate_metadata(cls, value: Dict) -> Dict:
        """Validates course metadata against schema."""
        from jsonschema import validate, ValidationError as JsonSchemaError
        try:
            validate(instance=value, schema=METADATA_SCHEMA)
        except JsonSchemaError as e:
            raise ValueError(f"Invalid metadata format: {str(e)}")
        return value

    @root_validator
    def validate_temporal(cls, values: Dict) -> Dict:
        """Validates temporal consistency of course validity dates."""
        valid_from = values.get('valid_from')
        valid_to = values.get('valid_to')

        if valid_from and valid_to and valid_from >= valid_to:
            raise ValueError("valid_to must be after valid_from")

        # Ensure minimum validity period (e.g., 1 day)
        if valid_from and valid_to:
            min_duration = timedelta(days=1)
            if valid_to - valid_from < min_duration:
                raise ValueError(f"Course must be valid for at least {min_duration}")

        return values

class CourseEquivalencySchema(BaseModel):
    """
    Schema for course equivalency validation with enhanced rules.
    """
    source_course_id: UUID = Field(..., description="Source course UUID")
    target_course_id: UUID = Field(..., description="Target course UUID")
    effective_date: datetime = Field(..., description="Equivalency start date")
    expiration_date: Optional[datetime] = Field(None, description="Equivalency end date")
    metadata: Dict = Field(default_factory=dict, description="Equivalency metadata")
    notes: Optional[str] = Field(None, description="Additional notes")
    validation_status: str = Field(
        default='pending',
        description="Validation status"
    )

    @root_validator
    def validate_course_relationship(cls, values: Dict) -> Dict:
        """Validates course equivalency relationship."""
        if values.get('source_course_id') == values.get('target_course_id'):
            raise ValueError("Source and target courses must be different")

        effective_date = values.get('effective_date')
        expiration_date = values.get('expiration_date')
        
        if effective_date and expiration_date and effective_date >= expiration_date:
            raise ValueError("expiration_date must be after effective_date")

        return values

    @validator('validation_status')
    def validate_status(cls, value: str) -> str:
        """Validates equivalency status."""
        valid_statuses = ['pending', 'approved', 'rejected', 'expired']
        if value not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
        return value

    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
            Decimal: str
        }