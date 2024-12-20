"""
Django REST Framework views for managing transfer requirements.
Implements comprehensive CRUD operations, versioning, validation, and search functionality.

Version: 1.0
"""

# Django REST Framework v3.14+
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.db import transaction
from django.core.cache import cache
from django.db.models import Q

# Internal imports
from apps.requirements.models import TransferRequirement
from apps.requirements.serializers import TransferRequirementSerializer
from utils.cache import CacheManager
from utils.exceptions import ValidationError, NotFoundError, PermissionDeniedError

import logging
from typing import Dict, Any, Optional
from decimal import Decimal

# Configure logging
logger = logging.getLogger(__name__)

# Cache configuration
CACHE_TIMEOUT = 60 * 15  # 15 minutes
VALIDATION_CACHE_TTL = 3600  # 1 hour

class TransferRequirementViewSet(viewsets.ModelViewSet):
    """
    Enhanced viewset for managing transfer requirements with comprehensive validation,
    caching, and performance optimization.
    """
    serializer_class = TransferRequirementSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['major_code', 'title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'major_code', 'validation_accuracy']
    cache_manager = CacheManager()

    def get_queryset(self):
        """
        Get filtered and cached queryset based on user permissions.
        Implements institution-specific filtering and query optimization.
        """
        cache_key = self.cache_manager.generate_cache_key(
            'requirement_queryset',
            user_id=self.request.user.id,
            filters=self.request.query_params
        )

        # Try to get cached queryset
        cached_queryset = cache.get(cache_key)
        if cached_queryset is not None:
            return cached_queryset

        # Build optimized base queryset
        queryset = TransferRequirement.objects.select_related(
            'source_institution',
            'target_institution'
        ).prefetch_related(
            'versions',
            'courses'
        )

        # Apply user-specific filters
        if not self.request.user.is_superuser:
            user_institutions = self.request.user.get_administered_institutions()
            queryset = queryset.filter(
                Q(source_institution__in=user_institutions) |
                Q(target_institution__in=user_institutions)
            )

        # Apply additional filters
        filters = {}
        if major_code := self.request.query_params.get('major_code'):
            filters['major_code'] = major_code
        if status_filter := self.request.query_params.get('status'):
            filters['status'] = status_filter
        if institution := self.request.query_params.get('institution'):
            filters['source_institution_id'] = institution

        queryset = queryset.filter(**filters)

        # Cache filtered queryset
        cache.set(cache_key, queryset, timeout=CACHE_TIMEOUT)
        return queryset

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Create new transfer requirement with version control and validation.
        Implements comprehensive data validation and error handling.
        """
        try:
            # Validate permissions
            if not self.request.user.has_perm('requirements.add_transferrequirement'):
                raise PermissionDeniedError(
                    message="Insufficient permissions to create requirements",
                    required_role="requirements_admin"
                )

            # Validate and create requirement
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # Create initial version
            requirement = serializer.save(
                created_by=request.user.id,
                version=1,
                metadata={
                    **request.data.get('metadata', {}),
                    'initial_version': True,
                    'created_by': str(request.user.id)
                }
            )

            # Invalidate relevant caches
            self._invalidate_requirement_caches(requirement)

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        except ValidationError as e:
            logger.error(f"Requirement creation failed: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error in requirement creation: {str(e)}", exc_info=True)
            raise ValidationError(message=f"Failed to create requirement: {str(e)}")

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """
        Update requirement with version control and comprehensive validation.
        Implements optimistic locking and conflict detection.
        """
        try:
            instance = self.get_object()

            # Validate permissions
            if not self._can_modify_requirement(instance):
                raise PermissionDeniedError(
                    message="Insufficient permissions to modify requirement",
                    required_role="institution_admin"
                )

            # Check version conflicts
            current_version = request.data.get('version')
            if current_version and instance.version != current_version:
                raise ValidationError(
                    message="Version conflict detected",
                    validation_errors={'version': 'Requirement has been modified'}
                )

            # Create new version
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            
            updated_requirement = serializer.save(
                updated_by=request.user.id,
                version=instance.version + 1,
                metadata={
                    **request.data.get('metadata', {}),
                    'updated_by': str(request.user.id),
                    'previous_version': str(instance.id)
                }
            )

            # Invalidate relevant caches
            self._invalidate_requirement_caches(updated_requirement)

            return Response(serializer.data)

        except ValidationError as e:
            logger.error(f"Requirement update failed: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error in requirement update: {str(e)}", exc_info=True)
            raise ValidationError(message=f"Failed to update requirement: {str(e)}")

    @action(detail=True, methods=['post'])
    def validate_courses(self, request, pk=None):
        """
        Validate courses against requirement with enhanced validation rules.
        Implements caching and accuracy tracking.
        """
        try:
            requirement = self.get_object()
            courses = request.data.get('courses', [])

            # Check cache for validation results
            cache_key = self.cache_manager.generate_cache_key(
                'course_validation',
                requirement_id=pk,
                courses=sorted(courses)
            )
            cached_result = cache.get(cache_key)
            if cached_result:
                return Response(cached_result)

            # Perform validation
            validation_results = requirement.validate_courses(courses)

            # Cache validation results
            cache.set(cache_key, validation_results, timeout=VALIDATION_CACHE_TTL)

            return Response(validation_results)

        except ValidationError as e:
            logger.error(f"Course validation failed: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error in course validation: {str(e)}", exc_info=True)
            raise ValidationError(message=f"Validation failed: {str(e)}")

    def _can_modify_requirement(self, requirement: TransferRequirement) -> bool:
        """
        Check if user has permission to modify requirement.
        
        Args:
            requirement: Requirement to check
            
        Returns:
            bool: Permission status
        """
        user = self.request.user
        if user.is_superuser:
            return True

        user_institutions = user.get_administered_institutions()
        return (
            requirement.source_institution in user_institutions or
            requirement.target_institution in user_institutions
        )

    def _invalidate_requirement_caches(self, requirement: TransferRequirement) -> None:
        """
        Invalidate all caches related to a requirement.
        
        Args:
            requirement: Requirement whose caches should be invalidated
        """
        cache_keys = [
            f'requirement:{requirement.id}',
            f'requirement_list:{requirement.source_institution_id}',
            f'requirement_list:{requirement.target_institution_id}',
            f'validation:{requirement.id}',
            f'requirement_queryset:{self.request.user.id}'
        ]
        
        for key in cache_keys:
            cache.delete(key)

    @method_decorator(cache_page(CACHE_TIMEOUT))
    def list(self, request, *args, **kwargs):
        """
        List requirements with caching and pagination.
        """
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(CACHE_TIMEOUT))
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve requirement with caching.
        """
        return super().retrieve(request, *args, **kwargs)