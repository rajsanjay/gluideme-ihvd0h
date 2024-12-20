"""
Django REST Framework views for course management in the Transfer Requirements Management System.
Implements comprehensive CRUD operations with caching, validation, and monitoring.

Version: 1.0
"""

# Django REST Framework imports - v3.14+
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.throttling import UserRateThrottle

# Django imports
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from django.db.models import Q

# Third-party imports
from prometheus_client import Counter, Histogram  # v0.16+
import meilisearch  # v0.20+
import logging

# Local imports
from apps.courses.models import Course, CourseEquivalency
from apps.courses.serializers import CourseSerializer, CourseEquivalencySerializer
from utils.cache import CacheManager, cached
from utils.exceptions import (
    ValidationError as AppValidationError,
    NotFoundError,
    PermissionDeniedError
)

# Configure logging
logger = logging.getLogger(__name__)

# Prometheus metrics
COURSE_OPERATIONS = Counter(
    'course_operations_total',
    'Total course operations',
    ['operation_type']
)
COURSE_OPERATION_LATENCY = Histogram(
    'course_operation_latency_seconds',
    'Course operation latency'
)

class CourseViewSet(viewsets.ModelViewSet):
    """
    Comprehensive ViewSet for managing course data with role-based access control,
    caching, search capabilities, and monitoring.
    """
    queryset = Course.objects.select_related('institution').all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    filter_backends = [filters.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['institution', 'status', 'credits', 'valid_from', 'valid_to']
    search_fields = ['code', 'name', 'description']
    ordering_fields = ['code', 'name', 'credits', 'updated_at']
    cache_manager = CacheManager()

    @COURSE_OPERATION_LATENCY.time()
    def get_queryset(self):
        """
        Get filtered queryset based on user role with caching.
        
        Returns:
            QuerySet: Filtered course queryset
        """
        cache_key = self.cache_manager.generate_cache_key(
            'course_queryset',
            user_id=str(self.request.user.id),
            filters=str(self.request.query_params)
        )
        
        cached_queryset = self.cache_manager.get(cache_key)
        if cached_queryset is not None:
            return cached_queryset

        queryset = super().get_queryset()

        # Apply role-based filtering
        if not self.request.user.is_superuser:
            if self.request.user.institution_id:
                queryset = queryset.filter(institution_id=self.request.user.institution_id)
            else:
                queryset = queryset.filter(status='active')

        # Cache filtered queryset
        self.cache_manager.set(cache_key, queryset, timeout=300)  # 5 minutes cache
        return queryset

    @COURSE_OPERATION_LATENCY.time()
    def perform_create(self, serializer):
        """
        Create course with validation and search indexing.
        
        Args:
            serializer: Validated course serializer
        """
        COURSE_OPERATIONS.labels(operation_type='create').inc()
        
        try:
            with transaction.atomic():
                # Validate institution permissions
                if not self.request.user.has_institution_permission(
                    serializer.validated_data['institution_id']
                ):
                    raise PermissionDeniedError(
                        message="No permission to create courses for this institution"
                    )

                # Create course
                course = serializer.save()
                
                # Index in search engine
                self._index_course(course)
                
                # Invalidate relevant caches
                self._invalidate_course_caches(course.institution_id)
                
                logger.info(
                    f"Course created: {course.code}",
                    extra={
                        'course_id': str(course.id),
                        'user_id': str(self.request.user.id)
                    }
                )

        except Exception as e:
            logger.error(
                f"Course creation failed: {str(e)}",
                exc_info=True,
                extra={'user_id': str(self.request.user.id)}
            )
            raise

    @COURSE_OPERATION_LATENCY.time()
    def perform_update(self, serializer):
        """
        Update course with validation and cache invalidation.
        
        Args:
            serializer: Validated course serializer
        """
        COURSE_OPERATIONS.labels(operation_type='update').inc()
        
        try:
            with transaction.atomic():
                # Validate permissions
                course = self.get_object()
                if not self.request.user.has_institution_permission(course.institution_id):
                    raise PermissionDeniedError(
                        message="No permission to update this course"
                    )

                # Update course
                updated_course = serializer.save()
                
                # Update search index
                self._index_course(updated_course)
                
                # Invalidate caches
                self._invalidate_course_caches(updated_course.institution_id)
                
                logger.info(
                    f"Course updated: {updated_course.code}",
                    extra={
                        'course_id': str(updated_course.id),
                        'user_id': str(self.request.user.id)
                    }
                )

        except Exception as e:
            logger.error(
                f"Course update failed: {str(e)}",
                exc_info=True,
                extra={'user_id': str(self.request.user.id)}
            )
            raise

    @action(detail=True, methods=['post'])
    @COURSE_OPERATION_LATENCY.time()
    def validate_transfer(self, request, pk=None):
        """
        Validate course transfer eligibility.
        
        Args:
            request: HTTP request
            pk: Course ID
            
        Returns:
            Response: Validation results
        """
        COURSE_OPERATIONS.labels(operation_type='validate_transfer').inc()
        
        try:
            course = self.get_object()
            target_institution_id = request.data.get('target_institution_id')
            validation_date = request.data.get('date') or timezone.now()

            if not target_institution_id:
                raise ValidationError({'target_institution_id': 'Required field'})

            # Check transfer validity
            is_valid, reasons = course.is_valid_for_transfer(
                validation_date,
                target_institution_id
            )

            return Response({
                'is_valid': is_valid,
                'reasons': reasons,
                'validated_at': timezone.now()
            })

        except Course.DoesNotExist:
            raise NotFoundError(
                message="Course not found",
                resource_type="Course",
                resource_id=pk
            )
        except Exception as e:
            logger.error(
                f"Transfer validation failed: {str(e)}",
                exc_info=True,
                extra={'course_id': pk, 'user_id': str(request.user.id)}
            )
            raise

    @action(detail=True, methods=['get'])
    @cached(timeout=3600)  # Cache for 1 hour
    def equivalencies(self, request, pk=None):
        """
        Get course equivalencies with caching.
        
        Args:
            request: HTTP request
            pk: Course ID
            
        Returns:
            Response: Course equivalencies
        """
        COURSE_OPERATIONS.labels(operation_type='get_equivalencies').inc()
        
        try:
            course = self.get_object()
            target_institution_id = request.query_params.get('institution_id')
            date = request.query_params.get('date')

            equivalencies = course.get_equivalent_courses(
                target_institution_id,
                date and timezone.parse_datetime(date)
            )

            serializer = CourseEquivalencySerializer(equivalencies, many=True)
            return Response(serializer.data)

        except Exception as e:
            logger.error(
                f"Failed to get equivalencies: {str(e)}",
                exc_info=True,
                extra={'course_id': pk, 'user_id': str(request.user.id)}
            )
            raise

    def _index_course(self, course):
        """
        Index course in MeiliSearch for enhanced search capabilities.
        
        Args:
            course: Course instance to index
        """
        try:
            client = meilisearch.Client('http://meilisearch:7700')
            index = client.index('courses')
            
            # Prepare searchable document
            document = {
                'id': str(course.id),
                'code': course.code,
                'name': course.name,
                'description': course.description,
                'institution_id': str(course.institution_id),
                'credits': float(course.credits),
                'status': course.status,
                'metadata': course.metadata
            }
            
            index.add_documents([document])

        except Exception as e:
            logger.error(
                f"Search indexing failed: {str(e)}",
                exc_info=True,
                extra={'course_id': str(course.id)}
            )
            # Don't raise - allow operation to continue even if indexing fails

    def _invalidate_course_caches(self, institution_id):
        """
        Invalidate related course caches.
        
        Args:
            institution_id: Institution ID for cache invalidation
        """
        cache_keys = [
            f'institution:{institution_id}:courses',
            f'course_queryset:institution:{institution_id}',
            'course_search_results'
        ]
        
        for key in cache_keys:
            self.cache_manager.delete(key)