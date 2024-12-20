"""
Enhanced ViewSet for user management in the Transfer Requirements Management System.
Implements secure user operations with caching, monitoring, and role-based access control.

Version: 1.0
"""

# Django REST Framework v3.14+
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

# Monitoring and Performance v0.16+
from prometheus_client import Counter, Histogram
import time

# Internal imports
from apps.users.models import User
from utils.cache import CacheManager
from utils.exceptions import ValidationError, NotFoundError

# Monitoring metrics
USER_OPERATIONS = Counter('user_operations_total', 'Total user operations', ['operation'])
OPERATION_LATENCY = Histogram('user_operation_latency_seconds', 'User operation latency')

def monitor_performance(func):
    """Decorator for monitoring operation performance and metrics."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        operation = func.__name__
        try:
            result = func(*args, **kwargs)
            USER_OPERATIONS.labels(operation=operation).inc()
            return result
        finally:
            OPERATION_LATENCY.observe(time.time() - start_time)
    return wrapper

class UserViewSet(viewsets.ModelViewSet):
    """
    Enhanced ViewSet for user management with comprehensive security,
    caching, and monitoring capabilities.
    
    Supports:
    - Role-based access control
    - Performance optimization through caching
    - Comprehensive monitoring and metrics
    - Secure data handling
    """
    
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    cache_manager = CacheManager()
    
    def get_serializer_class(self):
        """
        Get appropriate serializer based on action and user role.
        
        Returns:
            Serializer class based on context
        """
        if self.action in ['create', 'update', 'partial_update']:
            if self.request.user.role == 'admin':
                return UserAdminSerializer
            return UserUpdateSerializer
        return UserSerializer

    @monitor_performance
    def get_queryset(self):
        """
        Get filtered and cached queryset based on user role.
        
        Returns:
            QuerySet: Filtered user queryset
        
        Raises:
            PermissionDenied: If user lacks required permissions
        """
        cache_key = self.cache_manager.generate_cache_key(
            'user_queryset',
            user_id=str(self.request.user.id),
            role=self.request.user.role
        )
        
        # Try to get from cache
        cached_queryset = self.cache_manager.get(cache_key)
        if cached_queryset is not None:
            return User.objects.filter(id__in=cached_queryset)
        
        # Build filtered queryset based on role
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.role == 'admin':
            pass  # Admins can see all users
        elif user.role == 'institution_admin':
            queryset = queryset.filter(institution=user.institution)
        elif user.role == 'counselor':
            queryset = queryset.filter(
                institution=user.institution,
                role__in=['student', 'guest']
            )
        else:
            queryset = queryset.filter(id=user.id)  # Users can only see themselves
            
        # Cache filtered IDs
        self.cache_manager.set(
            cache_key,
            list(queryset.values_list('id', flat=True)),
            timeout=1800  # 30 minutes cache
        )
        
        return queryset

    @monitor_performance
    def perform_create(self, serializer):
        """
        Create user with enhanced validation and security checks.
        
        Args:
            serializer: Validated serializer instance
            
        Raises:
            PermissionDenied: If user lacks creation permissions
            ValidationError: If validation fails
        """
        user = self.request.user
        
        # Validate creation permissions
        if user.role not in ['admin', 'institution_admin']:
            raise PermissionDenied("Insufficient permissions to create users")
            
        # Additional validation for institution admins
        if user.role == 'institution_admin':
            if serializer.validated_data.get('role') in ['admin', 'institution_admin']:
                raise PermissionDenied("Cannot create admin users")
            serializer.validated_data['institution'] = user.institution
            
        try:
            serializer.save()
        except Exception as e:
            raise ValidationError(str(e))

    @monitor_performance
    def perform_update(self, serializer):
        """
        Update user with security validation and cache invalidation.
        
        Args:
            serializer: Validated serializer instance
            
        Raises:
            PermissionDenied: If user lacks update permissions
            ValidationError: If validation fails
        """
        user = self.request.user
        instance = self.get_object()
        
        # Validate update permissions
        if user.role not in ['admin', 'institution_admin']:
            if user.id != instance.id:
                raise PermissionDenied("Can only update own profile")
                
        # Additional validation for institution admins
        if user.role == 'institution_admin':
            if instance.role in ['admin', 'institution_admin']:
                raise PermissionDenied("Cannot modify admin users")
            if serializer.validated_data.get('institution') != user.institution:
                raise PermissionDenied("Cannot change user institution")
                
        try:
            # Perform update
            updated_instance = serializer.save()
            
            # Invalidate relevant caches
            self.cache_manager.delete(f"user:{updated_instance.id}")
            self.cache_manager.delete(f"user_queryset:{user.id}")
            
            return updated_instance
            
        except Exception as e:
            raise ValidationError(str(e))

    @monitor_performance
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activate a user account with security checks.
        
        Args:
            request: HTTP request
            pk: User ID
            
        Returns:
            Response: Activation status
            
        Raises:
            PermissionDenied: If user lacks activation permissions
            NotFoundError: If user not found
        """
        try:
            instance = self.get_object()
            
            # Validate activation permissions
            if not request.user.role in ['admin', 'institution_admin']:
                raise PermissionDenied("Insufficient permissions to activate users")
                
            if request.user.role == 'institution_admin':
                if instance.institution != request.user.institution:
                    raise PermissionDenied("Cannot activate users from other institutions")
                    
            # Perform activation
            instance.is_active = True
            instance.save()
            
            # Invalidate caches
            self.cache_manager.delete(f"user:{instance.id}")
            
            return Response({'status': 'user activated'})
            
        except User.DoesNotExist:
            raise NotFoundError("User not found")
        except Exception as e:
            raise ValidationError(str(e))

    @monitor_performance
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Deactivate a user account with security validation.
        
        Args:
            request: HTTP request
            pk: User ID
            
        Returns:
            Response: Deactivation status
            
        Raises:
            PermissionDenied: If user lacks deactivation permissions
            NotFoundError: If user not found
        """
        try:
            instance = self.get_object()
            
            # Validate deactivation permissions
            if not request.user.role == 'admin':
                raise PermissionDenied("Only administrators can deactivate users")
                
            # Prevent self-deactivation
            if instance.id == request.user.id:
                raise ValidationError("Cannot deactivate own account")
                
            # Perform deactivation
            instance.is_active = False
            instance.save()
            
            # Invalidate caches
            self.cache_manager.delete(f"user:{instance.id}")
            
            return Response({'status': 'user deactivated'})
            
        except User.DoesNotExist:
            raise NotFoundError("User not found")
        except Exception as e:
            raise ValidationError(str(e))