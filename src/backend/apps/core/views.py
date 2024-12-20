"""
Core view classes providing base functionality for the Transfer Requirements Management System.
Implements enhanced error handling, circuit breaker patterns, versioning capabilities, 
and comprehensive audit logging with security context tracking.

Version: 1.0
"""

# Django REST Framework v3.14+
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.core.cache import cache
from django.utils import timezone
from django.db import transaction
from circuit_breaker import circuit_breaker
from typing import Any, Dict, Optional, Type
import logging

# Internal imports
from apps.core.models import BaseModel
from apps.core.serializers import BaseModelSerializer
from utils.exceptions import (
    ValidationError, AuthenticationError, PermissionDeniedError,
    NotFoundError, ServerError
)

# Configure logger
logger = logging.getLogger(__name__)

class BaseViewSet(viewsets.ModelViewSet):
    """
    Enhanced base viewset with circuit breaker, caching, and comprehensive error handling.
    Implements core API functionality with optimized performance and security.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class: Type[BaseModelSerializer] = None
    queryset = None
    cache_timeout = 3600  # 1 hour default cache timeout
    
    def __init__(self, **kwargs):
        """Initialize enhanced base viewset with monitoring."""
        super().__init__(**kwargs)
        self.request_context = {}
        self.error_threshold = 5
        self.recovery_timeout = 30

    @circuit_breaker(failure_threshold=5, recovery_timeout=30)
    def get_queryset(self):
        """
        Get optimized and filtered queryset with caching.
        
        Returns:
            QuerySet: Filtered and optimized queryset
        """
        try:
            # Generate cache key
            cache_key = f"{self.__class__.__name__}_{self.action}"
            if self.request.user.id:
                cache_key += f"_{self.request.user.id}"

            # Check cache
            cached_queryset = cache.get(cache_key)
            if cached_queryset is not None:
                return cached_queryset

            # Get base queryset
            queryset = super().get_queryset()

            # Apply security filters
            queryset = self.apply_security_filters(queryset)

            # Apply optimizations
            queryset = self.optimize_queryset(queryset)

            # Cache results
            cache.set(cache_key, queryset, self.cache_timeout)

            return queryset

        except Exception as e:
            logger.error(
                "Queryset retrieval failed",
                extra={
                    "view": self.__class__.__name__,
                    "user_id": getattr(self.request.user, 'id', None),
                    "error": str(e)
                }
            )
            raise ServerError(
                message="Failed to retrieve data",
                technical_details={"error": str(e)}
            )

    def apply_security_filters(self, queryset):
        """
        Apply security-based filters to queryset.
        
        Args:
            queryset: Base queryset
            
        Returns:
            QuerySet: Security-filtered queryset
        """
        # Filter by active status
        queryset = queryset.filter(is_active=True)

        # Apply user-based filters
        if not self.request.user.is_superuser:
            if hasattr(queryset.model, 'created_by'):
                queryset = queryset.filter(created_by=self.request.user.id)

        return queryset

    def optimize_queryset(self, queryset):
        """
        Apply query optimizations.
        
        Args:
            queryset: Base queryset
            
        Returns:
            QuerySet: Optimized queryset
        """
        # Add select_related for foreign keys
        if hasattr(queryset.model, '_meta'):
            related_fields = [
                f.name for f in queryset.model._meta.fields 
                if f.is_relation
            ]
            if related_fields:
                queryset = queryset.select_related(*related_fields)

        return queryset

    def handle_exception(self, exc):
        """
        Enhanced exception handling with security context.
        
        Args:
            exc: Exception instance
            
        Returns:
            Response: Formatted error response
        """
        try:
            # Log exception with context
            logger.error(
                f"API Exception: {exc.__class__.__name__}",
                extra={
                    "view": self.__class__.__name__,
                    "action": self.action,
                    "user_id": getattr(self.request.user, 'id', None),
                    "error": str(exc)
                },
                exc_info=True
            )

            # Handle known exceptions
            if isinstance(exc, ValidationError):
                return Response(
                    exc.detail,
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif isinstance(exc, AuthenticationError):
                return Response(
                    exc.detail,
                    status=status.HTTP_401_UNAUTHORIZED
                )
            elif isinstance(exc, PermissionDeniedError):
                return Response(
                    exc.detail,
                    status=status.HTTP_403_FORBIDDEN
                )
            elif isinstance(exc, NotFoundError):
                return Response(
                    exc.detail,
                    status=status.HTTP_404_NOT_FOUND
                )

            # Handle unknown exceptions
            error = ServerError(
                message="An unexpected error occurred",
                technical_details={"error": str(exc)}
            )
            return Response(
                error.detail,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        except Exception as e:
            # Fallback error handling
            logger.critical(
                "Exception handler failed",
                extra={"error": str(e)},
                exc_info=True
            )
            return Response(
                {"error": "Critical system error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class VersionedViewSet(BaseViewSet):
    """
    Enhanced viewset for version-controlled resources.
    Implements temporal versioning with chain validation.
    """
    versioning_class = 'URLPathVersioning'
    version_param = 'version'

    def get_object(self):
        """
        Retrieve version-specific object instance.
        
        Returns:
            Model: Version-specific instance
        """
        try:
            # Get base object
            obj = super().get_object()

            # Check version parameter
            version = self.request.query_params.get(self.version_param)
            if version:
                return obj.get_version_at(version)

            return obj

        except Exception as e:
            raise NotFoundError(
                message="Version not found",
                resource_type=self.queryset.model.__name__,
                resource_id=self.kwargs.get('pk')
            )

    @transaction.atomic
    def create_version(self, request, pk=None):
        """
        Create new version with validation.
        
        Args:
            request: HTTP request
            pk: Primary key
            
        Returns:
            Response: Version creation response
        """
        try:
            # Get current instance
            instance = self.get_object()

            # Validate version transition
            serializer = self.get_serializer(instance)
            if not serializer.validate_version_transition(request.data):
                raise ValidationError(
                    message="Invalid version transition"
                )

            # Create new version
            new_version = serializer.create_version(request.data)

            return Response(
                self.get_serializer(new_version).data,
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            raise ValidationError(
                message="Version creation failed",
                validation_errors={"version": str(e)}
            )

class AuditViewSet(BaseViewSet):
    """
    Enhanced viewset with comprehensive audit logging.
    Implements detailed change tracking with security context.
    """
    audit_actions = ['create', 'update', 'partial_update', 'destroy']

    def get_serializer_context(self):
        """
        Enhanced serializer context with audit data.
        
        Returns:
            dict: Enhanced context
        """
        context = super().get_serializer_context()
        context.update({
            'user_id': self.request.user.id,
            'ip_address': self.request.META.get('REMOTE_ADDR'),
            'user_agent': self.request.META.get('HTTP_USER_AGENT')
        })
        return context

    def perform_create(self, serializer):
        """
        Create with enhanced audit trail.
        
        Args:
            serializer: Model serializer
        """
        try:
            with transaction.atomic():
                # Set audit fields
                serializer.validated_data['created_by'] = self.request.user.id
                
                # Create instance
                instance = serializer.save()

                # Log audit trail
                self.log_audit_trail(
                    instance,
                    'create',
                    serializer.validated_data
                )

        except Exception as e:
            raise ValidationError(
                message="Create operation failed",
                validation_errors={"audit": str(e)}
            )

    def perform_update(self, serializer):
        """
        Update with enhanced audit trail.
        
        Args:
            serializer: Model serializer
        """
        try:
            with transaction.atomic():
                # Get changes
                changes = {
                    field: value 
                    for field, value in serializer.validated_data.items()
                    if field != 'updated_by'
                }

                # Update instance
                instance = serializer.save(
                    updated_by=self.request.user.id
                )

                # Log audit trail
                self.log_audit_trail(
                    instance,
                    'update',
                    changes
                )

        except Exception as e:
            raise ValidationError(
                message="Update operation failed",
                validation_errors={"audit": str(e)}
            )

    def log_audit_trail(self, instance: BaseModel, action: str, 
                       changes: Dict[str, Any]) -> None:
        """
        Log detailed audit trail entry.
        
        Args:
            instance: Model instance
            action: Audit action
            changes: Changed data
        """
        try:
            audit_entry = {
                'timestamp': timezone.now().isoformat(),
                'action': action,
                'user_id': str(self.request.user.id),
                'changes': changes,
                'metadata': {
                    'ip_address': self.request.META.get('REMOTE_ADDR'),
                    'user_agent': self.request.META.get('HTTP_USER_AGENT'),
                    'session_id': self.request.session.session_key
                }
            }

            # Update instance audit log
            instance.log_change(
                action=action,
                changes=changes,
                user_id=self.request.user.id,
                category=action.upper()
            )

        except Exception as e:
            logger.error(
                "Audit logging failed",
                extra={
                    'instance_id': instance.id,
                    'action': action,
                    'error': str(e)
                }
            )