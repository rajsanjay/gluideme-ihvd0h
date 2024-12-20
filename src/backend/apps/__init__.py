"""
Root initialization module for all Django applications in the backend.

This package contains the core business logic components organized as Django applications
for the Transfer Requirements Management System. It provides explicit control over which
apps are publicly exposed for import throughout the project.

Available applications:
- core: Core functionality and shared utilities
- courses: Course management and equivalency logic
- institutions: Institution and organization management
- requirements: Transfer requirement definition and processing
- search: Search functionality and indexing
- users: User management and authentication
- validation: Course and requirement validation logic

Version: 1.0.0
"""

# Explicitly declare which Django app modules are available for import from this package
__all__ = [
    "core",
    "courses", 
    "institutions",
    "requirements",
    "search",
    "users",
    "validation"
]