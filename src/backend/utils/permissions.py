"""
Custom permission classes implementing comprehensive role-based access control (RBAC)
with granular permission checks, caching, and audit logging.

Version: 1.0
"""

import abc
import logging
from typing import Optional, Set
from rest_framework.permissions import BasePermission  # v3.14+
from django.utils.functional import cached_property  # v4.2+
from apps.users.models import User
from utils.exceptions import PermissionDeniedError
from utils.cache import cached

# Configure logging
logger = logging.getLogger(__name__)

# Role constants for permission checks
ADMIN_ROLES = {'admin', 'superadmin'}
INSTITUTION_ADMIN_ROLES = {'admin', 'superadmin', 'institution_admin'}
COUNSELOR_ROLES = {'admin', 'superadmin', 'institution_admin', 'counselor'}

# Cache timeout for permission results (5 minutes)
PERMISSION_CACHE_TTL = 300

class BaseRolePermission(BasePermission, abc.ABC):
    """
    Abstract base class for role-based permissions with caching and audit logging.
    Implements core permission logic with performance optimizations.
    """

    def __init__(self) -> None:
        """Initialize permission class with logging configuration."""
        super().__init__()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @cached_property
    def allowed_roles(self) -> Set[str]:
        """
        Define allowed roles for the permission class.
        Must be implemented by subclasses.
        
        Returns:
            Set[str]: Set of allowed role names
        """
        raise NotImplementedError("Subclasses must implement allowed_roles")

    @cached(ttl=PERMISSION_CACHE_TTL, prefix="base_permission")
    def has_permission(self, request, view) -> bool:
        """
        Base permission check with caching and audit logging.
        
        Args:
            request: The incoming request
            view: The view being accessed
            
        Returns:
            bool: Whether permission is granted
            
        Raises:
            PermissionDeniedError: If permission check fails
        """
        try:
            # Log permission check attempt
            self.logger.info(
                "Permission check initiated",
                extra={
                    "user_id": getattr(request.user, "id", None),
                    "view": view.__class__.__name__,
                    "method": request.method,
                }
            )

            # Verify user authentication
            if not request.user or not request.user.is_authenticated:
                raise PermissionDeniedError(
                    message="Authentication required",
                    required_role=str(self.allowed_roles)
                )

            # Check user role against allowed roles
            has_role = request.user.role in self.allowed_roles
            
            # Log permission result
            self.logger.info(
                f"Permission {'granted' if has_role else 'denied'}",
                extra={
                    "user_id": request.user.id,
                    "user_role": request.user.role,
                    "allowed_roles": list(self.allowed_roles),
                }
            )

            return has_role

        except Exception as e:
            self.logger.error(
                "Permission check failed",
                extra={
                    "error": str(e),
                    "user_id": getattr(request.user, "id", None),
                },
                exc_info=True
            )
            raise

class IsAdmin(BaseRolePermission):
    """
    Permission class for admin role with enhanced validation.
    Implements strict admin permission checks with super admin validation.
    """

    @cached_property
    def allowed_roles(self) -> Set[str]:
        """Define admin roles."""
        return ADMIN_ROLES

    @cached(ttl=PERMISSION_CACHE_TTL, prefix="admin_permission")
    def has_permission(self, request, view) -> bool:
        """
        Check admin permission with super admin validation.
        
        Args:
            request: The incoming request
            view: The view being accessed
            
        Returns:
            bool: Whether admin permission is granted
        """
        try:
            # Log admin permission check
            self.logger.info(
                "Admin permission check initiated",
                extra={
                    "user_id": getattr(request.user, "id", None),
                    "view": view.__class__.__name__,
                }
            )

            # Verify user authentication
            if not request.user or not request.user.is_authenticated:
                raise PermissionDeniedError(
                    message="Authentication required for admin access",
                    required_role="admin"
                )

            # Check admin role
            is_admin = request.user.role in ADMIN_ROLES

            # Additional validation for super admin actions
            if getattr(view, 'require_superadmin', False) and request.user.role != 'superadmin':
                raise PermissionDeniedError(
                    message="Super admin access required",
                    required_role="superadmin"
                )

            # Log permission result
            self.logger.info(
                f"Admin permission {'granted' if is_admin else 'denied'}",
                extra={
                    "user_id": request.user.id,
                    "user_role": request.user.role,
                }
            )

            return is_admin

        except Exception as e:
            self.logger.error(
                "Admin permission check failed",
                extra={"error": str(e)},
                exc_info=True
            )
            raise

class IsInstitutionAdmin(BaseRolePermission):
    """
    Permission class for institution admin with institution validation.
    Implements institution-specific permission checks with caching.
    """

    @cached_property
    def allowed_roles(self) -> Set[str]:
        """Define institution admin roles."""
        return INSTITUTION_ADMIN_ROLES

    @cached(ttl=PERMISSION_CACHE_TTL, prefix="institution_admin_permission")
    def has_permission(self, request, view) -> bool:
        """
        Check institution admin permission with institution validation.
        
        Args:
            request: The incoming request
            view: The view being accessed
            
        Returns:
            bool: Whether institution admin permission is granted
        """
        try:
            # Log institution admin check
            self.logger.info(
                "Institution admin permission check initiated",
                extra={
                    "user_id": getattr(request.user, "id", None),
                    "view": view.__class__.__name__,
                }
            )

            # Verify user authentication
            if not request.user or not request.user.is_authenticated:
                raise PermissionDeniedError(
                    message="Authentication required for institution admin access",
                    required_role="institution_admin"
                )

            # Check institution admin role
            has_role = request.user.role in INSTITUTION_ADMIN_ROLES

            # Validate institution access if institution_id provided
            institution_id = request.parser_context.get('kwargs', {}).get('institution_id')
            if institution_id and not request.user.has_institution_access(institution_id):
                raise PermissionDeniedError(
                    message="No access to this institution",
                    required_role="institution_admin"
                )

            # Log permission result
            self.logger.info(
                f"Institution admin permission {'granted' if has_role else 'denied'}",
                extra={
                    "user_id": request.user.id,
                    "user_role": request.user.role,
                    "institution_id": institution_id,
                }
            )

            return has_role

        except Exception as e:
            self.logger.error(
                "Institution admin permission check failed",
                extra={"error": str(e)},
                exc_info=True
            )
            raise

    @cached(ttl=PERMISSION_CACHE_TTL, prefix="institution_object_permission")
    def has_object_permission(self, request, view, obj) -> bool:
        """
        Check institution-specific object permission.
        
        Args:
            request: The incoming request
            view: The view being accessed
            obj: The object being accessed
            
        Returns:
            bool: Whether object permission is granted
        """
        try:
            # Log object permission check
            self.logger.info(
                "Institution object permission check initiated",
                extra={
                    "user_id": request.user.id,
                    "object_type": obj.__class__.__name__,
                }
            )

            # Get institution from object
            institution_id = getattr(obj, 'institution_id', None)
            if not institution_id:
                return False

            # Validate institution access
            has_access = request.user.has_institution_access(institution_id)

            # Log permission result
            self.logger.info(
                f"Institution object permission {'granted' if has_access else 'denied'}",
                extra={
                    "user_id": request.user.id,
                    "institution_id": institution_id,
                }
            )

            return has_access

        except Exception as e:
            self.logger.error(
                "Institution object permission check failed",
                extra={"error": str(e)},
                exc_info=True
            )
            raise