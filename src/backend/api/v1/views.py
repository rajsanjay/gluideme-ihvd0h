"""
Django REST Framework views implementing the API v1 endpoints for transfer requirements management system.
Implements comprehensive validation, caching, and error handling with 99.99% accuracy target.

Version: 1.0
"""

from rest_framework import viewsets, permissions, filters, status  # v3.14+
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.cache import cache  # v4.2+
from django.utils import timezone
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from api.v1.serializers import (
    TransferRequirementSerializer,
    CourseSerializer
)
from apps.requirements.models import TransferRequirement
from apps.courses.models import Course
from utils.exceptions import ValidationError, NotFoundError
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Cache TTL settings
VALIDATION_CACHE_TTL = 3600  # 1 hour
QUERYSET_CACHE_TTL = 300    # 5 minutes

class TransferRequirementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing transfer requirements with comprehensive validation,
    caching, and audit logging.
    """
    serializer_class = TransferRequirementSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['source_institution', 'target_institution', 'major_code', 'status']
    search_fields = ['title', 'description', 'major_code']
    ordering_fields = ['effective_date', 'created_at', 'validation_accuracy']

    def get_queryset(self):
        """
        Get filtered queryset with caching and optimized joins.
        """
        cache_key = f"requirement_queryset:{self.request.user.id}:{hash(str(self.request.query_params))}"
        cached_queryset = cache.get(cache_key)

        if cached_queryset is not None:
            return cached_queryset

        # Base queryset with optimized joins
        queryset = TransferRequirement.objects.select_related(
            'source_institution',
            'target_institution'
        ).prefetch_related(
            'source_requirements',
            'target_requirements'
        ).filter(is_active=True)

        # Apply institution filtering for non-admin users
        if not self.request.user.is_staff:
            user_institutions = self.request.user.institutions.values_list('id', flat=True)
            queryset = queryset.filter(
                models.Q(source_institution__in=user_institutions) |
                models.Q(target_institution__in=user_institutions)
            )

        cache.set(cache_key, queryset, QUERYSET_CACHE_TTL)
        return queryset

    @action(detail=True, methods=['post'])
    def validate_courses(self, request, pk=None) -> Response:
        """
        Validate courses against requirement with comprehensive validation.
        
        Args:
            request: Request containing course list
            pk: Requirement ID
            
        Returns:
            Response: Detailed validation results
        """
        try:
            # Check cache
            cache_key = f"course_validation:{pk}:{hash(str(request.data))}"
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return Response(cached_result)

            # Get requirement
            requirement = self.get_object()
            if not requirement.is_active()[0]:
                raise ValidationError(
                    message="Requirement is not active",
                    validation_errors={'status': 'inactive'}
                )

            # Validate course list
            course_ids = request.data.get('courses', [])
            courses = Course.objects.filter(id__in=course_ids)
            if len(courses) != len(course_ids):
                raise ValidationError(
                    message="One or more courses not found",
                    validation_errors={'courses': 'invalid_ids'}
                )

            # Perform validation
            validation_results = requirement.validate_courses(courses)
            
            # Cache results
            cache.set(cache_key, validation_results, VALIDATION_CACHE_TTL)
            
            # Log validation attempt
            logger.info(
                f"Course validation performed",
                extra={
                    'requirement_id': pk,
                    'course_count': len(courses),
                    'validation_success': validation_results['valid']
                }
            )

            return Response(validation_results)

        except ValidationError as e:
            raise
        except Exception as e:
            logger.error(f"Validation failed: {str(e)}", exc_info=True)
            raise ValidationError(
                message="Validation failed",
                validation_errors={'general': str(e)}
            )

class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing course data with transfer validity checking and caching.
    """
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['institution', 'code', 'credits', 'status']
    search_fields = ['name', 'description', 'code']

    def get_queryset(self):
        """
        Get filtered queryset with caching and optimized joins.
        """
        cache_key = f"course_queryset:{self.request.user.id}:{hash(str(self.request.query_params))}"
        cached_queryset = cache.get(cache_key)

        if cached_queryset is not None:
            return cached_queryset

        # Base queryset with optimized joins
        queryset = Course.objects.select_related(
            'institution'
        ).prefetch_related(
            'prerequisites'
        ).filter(is_active=True)

        # Apply institution filtering for non-admin users
        if not self.request.user.is_staff:
            user_institutions = self.request.user.institutions.values_list('id', flat=True)
            queryset = queryset.filter(institution__in=user_institutions)

        cache.set(cache_key, queryset, QUERYSET_CACHE_TTL)
        return queryset

    @action(detail=True, methods=['post'])
    def check_transfer_validity(self, request, pk=None) -> Response:
        """
        Check if course is valid for transfer with comprehensive validation.
        
        Args:
            request: Request containing target institution
            pk: Course ID
            
        Returns:
            Response: Detailed transfer validity status
        """
        try:
            # Check cache
            cache_key = f"transfer_validity:{pk}:{hash(str(request.data))}"
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return Response(cached_result)

            # Get course
            course = self.get_object()
            
            # Get target institution
            target_institution_id = request.data.get('target_institution')
            target_institution = Institution.objects.get(id=target_institution_id)

            # Check validity
            is_valid, reasons = course.is_valid_for_transfer(
                timezone.now(),
                target_institution
            )

            # Format response
            validity_result = {
                'valid': is_valid,
                'reasons': reasons,
                'checked_at': timezone.now().isoformat(),
                'course_code': course.code,
                'target_institution': target_institution.code
            }

            # Cache result
            cache.set(cache_key, validity_result, VALIDATION_CACHE_TTL)

            # Log check
            logger.info(
                f"Transfer validity checked",
                extra={
                    'course_id': pk,
                    'target_institution': target_institution_id,
                    'is_valid': is_valid
                }
            )

            return Response(validity_result)

        except Course.DoesNotExist:
            raise NotFoundError(
                message="Course not found",
                resource_type="Course",
                resource_id=pk
            )
        except Institution.DoesNotExist:
            raise ValidationError(
                message="Target institution not found",
                validation_errors={'target_institution': 'invalid_id'}
            )
        except Exception as e:
            logger.error(f"Validity check failed: {str(e)}", exc_info=True)
            raise ValidationError(
                message="Validity check failed",
                validation_errors={'general': str(e)}
            )