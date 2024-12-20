"""
Django REST Framework views for managing institutions and institution agreements.
Implements comprehensive validation, caching, and role-based access control.

Version: 1.0
"""

from rest_framework import viewsets  # v3.14+
from rest_framework import filters  # v3.14+
from rest_framework.response import Response  # v3.14+
from rest_framework import status  # v3.14+
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.core.cache import cache
from django.utils import timezone
from typing import Dict, Any, Optional

from apps.institutions.models import Institution, InstitutionAgreement
from apps.institutions.serializers import InstitutionSerializer, InstitutionAgreementSerializer
from utils.cache import CacheManager
from utils.exceptions import ValidationError, NotFoundError, PermissionDeniedError

# Initialize cache manager
cache_manager = CacheManager()

class InstitutionViewSet(viewsets.ModelViewSet):
    """
    Enhanced viewset for managing Institution model instances with caching,
    validation, and audit logging.
    """
    queryset = Institution.objects.select_related('type').prefetch_related('courses')
    serializer_class = InstitutionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'type', 'status']
    ordering_fields = ['name', 'type', 'status', 'created_at']

    def get_queryset(self):
        """
        Get filtered and cached queryset based on user role.
        
        Returns:
            QuerySet: Filtered institution queryset
        """
        cache_key = f"institution_queryset:{self.request.user.id}"
        cached_queryset = cache.get(cache_key)

        if cached_queryset is not None:
            return cached_queryset

        queryset = super().get_queryset()

        # Apply role-based filtering
        if not self.request.user.is_superuser:
            if hasattr(self.request.user, 'institution'):
                queryset = queryset.filter(id=self.request.user.institution.id)
            else:
                queryset = queryset.filter(is_active=True)

        # Cache queryset for 15 minutes
        cache.set(cache_key, queryset, timeout=900)
        return queryset

    @transaction.atomic
    def perform_create(self, serializer):
        """
        Create institution with validation and audit logging.
        
        Args:
            serializer: Institution serializer instance
        """
        try:
            # Validate user permissions
            if not self.request.user.has_perm('institutions.add_institution'):
                raise PermissionDeniedError(
                    message="Insufficient permissions to create institution",
                    required_role="Institution Admin"
                )

            # Create institution
            institution = serializer.save(
                created_by=self.request.user.id,
                metadata={
                    'created_from_ip': self.request.META.get('REMOTE_ADDR'),
                    'created_by_email': self.request.user.email
                }
            )

            # Invalidate relevant caches
            cache_keys = [
                f"institution_queryset:{self.request.user.id}",
                "institution_list",
                f"institution:{institution.id}"
            ]
            cache.delete_many(cache_keys)

            return institution

        except Exception as e:
            raise ValidationError(
                message="Failed to create institution",
                validation_errors={'creation': str(e)}
            )

    @transaction.atomic
    def perform_update(self, serializer):
        """
        Update institution with version control and audit logging.
        
        Args:
            serializer: Institution serializer instance
        """
        try:
            # Validate user permissions
            if not self.request.user.has_perm('institutions.change_institution'):
                raise PermissionDeniedError(
                    message="Insufficient permissions to update institution",
                    required_role="Institution Admin"
                )

            # Create new version
            institution = serializer.create_version(
                data=serializer.validated_data,
                reason=self.request.data.get('change_reason', 'Manual update'),
                effective_date=timezone.now()
            )

            # Invalidate caches
            cache_keys = [
                f"institution_queryset:{self.request.user.id}",
                "institution_list",
                f"institution:{institution.id}"
            ]
            cache.delete_many(cache_keys)

            return institution

        except Exception as e:
            raise ValidationError(
                message="Failed to update institution",
                validation_errors={'update': str(e)}
            )

    @action(detail=True, methods=['get'])
    @cache_manager.cached(timeout=1800)
    def active_courses(self, request, pk=None):
        """
        Get active courses for institution with caching.
        
        Args:
            request: HTTP request
            pk: Institution ID
            
        Returns:
            Response: List of active courses
        """
        try:
            institution = self.get_object()
            courses = institution.get_active_courses()
            return Response({
                'count': len(courses),
                'results': courses
            })
        except Institution.DoesNotExist:
            raise NotFoundError(
                message="Institution not found",
                resource_type="Institution",
                resource_id=pk
            )

class InstitutionAgreementViewSet(viewsets.ModelViewSet):
    """
    Enhanced viewset for managing InstitutionAgreement instances with
    validation and version control.
    """
    queryset = InstitutionAgreement.objects.select_related(
        'source_institution',
        'target_institution'
    )
    serializer_class = InstitutionAgreementSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'source_institution__name',
        'target_institution__name',
        'agreement_type',
        'status'
    ]
    ordering_fields = [
        'effective_date',
        'expiration_date',
        'status',
        'created_at'
    ]

    def get_queryset(self):
        """
        Get filtered agreement queryset based on user role.
        
        Returns:
            QuerySet: Filtered agreement queryset
        """
        cache_key = f"agreement_queryset:{self.request.user.id}"
        cached_queryset = cache.get(cache_key)

        if cached_queryset is not None:
            return cached_queryset

        queryset = super().get_queryset()

        # Apply role-based filtering
        if not self.request.user.is_superuser:
            if hasattr(self.request.user, 'institution'):
                queryset = queryset.filter(
                    source_institution=self.request.user.institution
                )
            else:
                queryset = queryset.filter(is_active=True)

        # Cache queryset for 15 minutes
        cache.set(cache_key, queryset, timeout=900)
        return queryset

    @transaction.atomic
    def perform_create(self, serializer):
        """
        Create agreement with validation and audit logging.
        
        Args:
            serializer: Agreement serializer instance
        """
        try:
            # Validate user permissions
            if not self.request.user.has_perm('institutions.add_institutionagreement'):
                raise PermissionDeniedError(
                    message="Insufficient permissions to create agreement",
                    required_role="Institution Admin"
                )

            # Create agreement
            agreement = serializer.save(
                created_by=self.request.user.id,
                metadata={
                    'created_from_ip': self.request.META.get('REMOTE_ADDR'),
                    'created_by_email': self.request.user.email
                }
            )

            # Invalidate caches
            cache_keys = [
                f"agreement_queryset:{self.request.user.id}",
                "agreement_list",
                f"agreement:{agreement.id}"
            ]
            cache.delete_many(cache_keys)

            return agreement

        except Exception as e:
            raise ValidationError(
                message="Failed to create agreement",
                validation_errors={'creation': str(e)}
            )

    @action(detail=True, methods=['get'])
    @cache_manager.cached(timeout=1800)
    def validate_dates(self, request, pk=None):
        """
        Validate agreement dates for conflicts.
        
        Args:
            request: HTTP request
            pk: Agreement ID
            
        Returns:
            Response: Validation results
        """
        try:
            agreement = self.get_object()
            validation_result = agreement.validate_dates()
            return Response({
                'is_valid': validation_result,
                'agreement_id': agreement.id
            })
        except InstitutionAgreement.DoesNotExist:
            raise NotFoundError(
                message="Agreement not found",
                resource_type="InstitutionAgreement",
                resource_id=pk
            )