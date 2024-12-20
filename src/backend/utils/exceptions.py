"""
Custom exception classes for standardized error handling across the Transfer Requirements Management System.
Implements a comprehensive hierarchy of exceptions with consistent response formats and logging integration.

Version: 1.0
"""

# rest_framework v3.14+
from rest_framework import status
from rest_framework.exceptions import APIException
import logging
import uuid
import json
from typing import Dict, Optional, Any

# Configure logger
logger = logging.getLogger(__name__)

class BaseAPIException(APIException):
    """
    Base exception class for all API errors with standardized error response format.
    Provides consistent error handling and logging across the application.
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_message = "An unexpected error occurred"
    
    def __init__(self, message: Optional[str] = None, details: Optional[Dict] = None, error_code: Optional[str] = None) -> None:
        """
        Initialize base API exception with standardized error structure.
        
        Args:
            message (str, optional): Custom error message
            details (dict, optional): Additional error context
            error_code (str, optional): Unique error identifier
        """
        self.message = message or self.default_message
        self.error_details = details or {}
        self.error_code = error_code or f"ERR_{uuid.uuid4().hex[:8].upper()}"
        
        # Format standardized error response
        self.detail = {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.error_details,
            "status": self.status_code
        }
        
        # Log error with context
        logger.error(
            f"API Exception: {self.error_code}",
            extra={
                "error_code": self.error_code,
                "message": self.message,
                "details": json.dumps(self.error_details),
                "status_code": self.status_code
            }
        )
        
        super().__init__(detail=self.detail)

class ValidationError(BaseAPIException):
    """
    Exception for data validation errors with field-level error details.
    Used for form validation, data integrity, and business rule violations.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_message = "Invalid data provided"
    
    def __init__(self, message: Optional[str] = None, validation_errors: Dict = None, error_code: Optional[str] = None) -> None:
        """
        Initialize validation error with field-specific error details.
        
        Args:
            message (str, optional): Custom validation error message
            validation_errors (dict): Field-specific validation errors
            error_code (str, optional): Unique error identifier
        """
        self.validation_errors = validation_errors or {}
        formatted_details = {
            "validation_errors": self.validation_errors,
            "fields_with_errors": list(self.validation_errors.keys())
        }
        
        error_code = error_code or f"VAL_{uuid.uuid4().hex[:8].upper()}"
        super().__init__(message=message, details=formatted_details, error_code=error_code)

class AuthenticationError(BaseAPIException):
    """
    Exception for authentication failures including JWT and session issues.
    Handles token expiration, invalid credentials, and session management errors.
    """
    status_code = status.HTTP_401_UNAUTHORIZED
    default_message = "Authentication failed"
    
    def __init__(self, message: Optional[str] = None, auth_type: str = "token", error_code: Optional[str] = None) -> None:
        """
        Initialize authentication error with auth-specific context.
        
        Args:
            message (str, optional): Custom authentication error message
            auth_type (str): Authentication method that failed (token/session)
            error_code (str, optional): Unique error identifier
        """
        auth_details = {
            "auth_type": auth_type,
            "requires_reauthentication": True
        }
        
        error_code = error_code or f"AUTH_{uuid.uuid4().hex[:8].upper()}"
        super().__init__(message=message, details=auth_details, error_code=error_code)

class PermissionDeniedError(BaseAPIException):
    """
    Exception for authorization failures with role-based context.
    Handles insufficient permissions and role-based access control violations.
    """
    status_code = status.HTTP_403_FORBIDDEN
    default_message = "Permission denied"
    
    def __init__(self, message: Optional[str] = None, required_role: str = None, error_code: Optional[str] = None) -> None:
        """
        Initialize permission denied error with role context.
        
        Args:
            message (str, optional): Custom permission error message
            required_role (str): Role required for the action
            error_code (str, optional): Unique error identifier
        """
        permission_details = {
            "required_role": required_role,
            "access_level": "insufficient"
        }
        
        error_code = error_code or f"PERM_{uuid.uuid4().hex[:8].upper()}"
        super().__init__(message=message, details=permission_details, error_code=error_code)

class NotFoundError(BaseAPIException):
    """
    Exception for resource not found errors with resource context.
    Handles missing database records, files, and other resources.
    """
    status_code = status.HTTP_404_NOT_FOUND
    default_message = "Resource not found"
    
    def __init__(self, message: Optional[str] = None, resource_type: str = None, 
                 resource_id: Any = None, error_code: Optional[str] = None) -> None:
        """
        Initialize not found error with resource context.
        
        Args:
            message (str, optional): Custom not found message
            resource_type (str): Type of resource that wasn't found
            resource_id: Identifier of the missing resource
            error_code (str, optional): Unique error identifier
        """
        resource_details = {
            "resource_type": resource_type,
            "resource_id": str(resource_id),
            "searchable": True
        }
        
        error_code = error_code or f"NF_{uuid.uuid4().hex[:8].upper()}"
        super().__init__(message=message, details=resource_details, error_code=error_code)

class ServerError(BaseAPIException):
    """
    Exception for internal server errors with error tracking.
    Handles system errors, external service failures, and unexpected conditions.
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_message = "Internal server error"
    
    def __init__(self, message: Optional[str] = None, error_id: Optional[str] = None,
                 technical_details: Dict = None, error_code: Optional[str] = None) -> None:
        """
        Initialize server error with error tracking.
        
        Args:
            message (str, optional): Custom error message
            error_id (str, optional): Unique error tracking ID
            technical_details (dict): Technical error context (sanitized)
            error_code (str, optional): Unique error identifier
        """
        self.error_id = error_id or uuid.uuid4().hex
        
        # Sanitize technical details to remove sensitive information
        safe_technical_details = self._sanitize_technical_details(technical_details or {})
        
        server_details = {
            "error_id": self.error_id,
            "technical_details": safe_technical_details,
            "recoverable": False
        }
        
        error_code = error_code or f"SRV_{uuid.uuid4().hex[:8].upper()}"
        super().__init__(message=message, details=server_details, error_code=error_code)
        
        # Log detailed error information for monitoring
        logger.critical(
            f"Server Error: {self.error_id}",
            extra={
                "error_id": self.error_id,
                "error_code": error_code,
                "technical_details": json.dumps(safe_technical_details)
            },
            exc_info=True
        )
    
    def _sanitize_technical_details(self, details: Dict) -> Dict:
        """
        Remove sensitive information from technical details.
        
        Args:
            details (dict): Raw technical error details
            
        Returns:
            dict: Sanitized technical details
        """
        sensitive_keys = {'password', 'token', 'secret', 'key', 'credential'}
        sanitized = {}
        
        for key, value in details.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = '[REDACTED]'
            else:
                sanitized[key] = value
        
        return sanitized
```

This implementation provides a comprehensive exception handling system with the following key features:

1. Hierarchical exception structure with a base class and specialized exceptions
2. Standardized error response format across all exceptions
3. Automatic error code generation and tracking
4. Detailed logging integration with context
5. Sanitization of sensitive information
6. Support for field-level validation errors
7. Role-based authorization context
8. Resource-specific error details
9. Error tracking and monitoring integration

The exceptions follow REST best practices and provide consistent error handling across the Transfer Requirements Management System. Each exception class includes detailed documentation and type hints for better development experience.

The error response format is standardized as:
```python
{
    "error_code": "unique_error_code",
    "message": "Human readable error message",
    "details": {
        # Context-specific error details
    },
    "status": status_code
}