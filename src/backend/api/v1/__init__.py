"""Transfer Requirements Management System API v1

This module initializes the v1 API package and provides version metadata for the REST API.
It defines constants used for API documentation, version tracking, and URI routing.

Version information follows semantic versioning (major.minor.patch).
API version identifier is used for URL construction in the format /api/v1/.

Constants:
    __version__: Semantic version number
    __api_name__: Human-readable API name
    __api_version__: Version identifier for routing
    __api_description__: Comprehensive API description

Usage:
    from api.v1 import __version__, __api_name__
    print(f'Using {__api_name__} version {__version__}')

Security:
    Version information exposure is controlled for security monitoring and compliance.
    Version numbers should not reveal detailed implementation information.

Author:
    Transfer Requirements Management System Team

Copyright:
    2023 Transfer Requirements Management System
"""

# API Version Information
# Following semantic versioning: major.minor.patch
__version__ = '1.0.0'

# API Metadata
# Used in documentation headers, error messages, and API metadata
__api_name__ = 'Transfer Requirements Management API'

# API Version Identifier
# Used by custom router for URL construction and version-specific routing
__api_version__ = 'v1'

# API Description
# Used in OpenAPI documentation to describe API capabilities
__api_description__ = '''REST API for managing transfer requirements between California educational institutions. \
Provides endpoints for requirement management, course validation, and transfer pathway planning. \
Supports automated requirement parsing, real-time validation, and multi-institution search capabilities.'''

# Note: All exports are intentionally exposed for use in API routing and documentation
__all__ = [
    '__version__',
    '__api_name__',
    '__api_version__',
    '__api_description__'
]