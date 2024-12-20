"""
Custom middleware components for request/response processing in the Transfer Requirements Management System.
Implements comprehensive logging, security headers, and exception handling with CloudWatch integration.

Version: 1.0
"""

# Standard library imports - v3.11+
import time
import logging
import json
import uuid
from typing import Callable, Dict, Optional

# Django imports - v4.2+
from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse

# Third-party imports
import boto3  # v1.26+

# Internal imports
from utils.exceptions import BaseAPIException
from utils.cache import cache_set

# Configure logging
logger = logging.getLogger(__name__)

class RequestLoggingMiddleware:
    """
    Enhanced middleware for logging request/response details and performance metrics
    with CloudWatch integration and correlation tracking.
    """
    
    def __init__(self, get_response: Callable) -> None:
        """
        Initialize middleware with CloudWatch integration and logging setup.
        
        Args:
            get_response: Callable to process the request
        """
        self.get_response = get_response
        self.logger = logging.getLogger('request.monitoring')
        
        # Initialize CloudWatch client
        self.cloudwatch_client = boto3.client(
            'cloudwatch',
            region_name=settings.AWS_REGION
        )
        
        # Configure sampling rate for detailed logging
        self.sample_rate = getattr(settings, 'REQUEST_LOGGING_SAMPLE_RATE', 0.1)
        
    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        Process request with enhanced logging and performance tracking.
        
        Args:
            request: The incoming HTTP request
            
        Returns:
            HttpResponse with correlation ID header
        """
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        request.correlation_id = correlation_id
        
        # Apply sampling logic
        should_log_detail = uuid.uuid4().int % 100 < (self.sample_rate * 100)
        
        # Record request start time
        start_time = time.time()
        
        if should_log_detail:
            # Log detailed request context
            self.logger.info(
                'Request started',
                extra={
                    'correlation_id': correlation_id,
                    'method': request.method,
                    'path': request.path,
                    'query_params': dict(request.GET),
                    'remote_addr': request.META.get('REMOTE_ADDR'),
                    'user_agent': request.META.get('HTTP_USER_AGENT')
                }
            )
        
        # Process request
        response = self.get_response(request)
        
        # Calculate request duration
        duration = time.time() - start_time
        
        # Send metrics to CloudWatch
        self.cloudwatch_client.put_metric_data(
            Namespace='TRMS/API',
            MetricData=[
                {
                    'MetricName': 'RequestDuration',
                    'Value': duration,
                    'Unit': 'Seconds',
                    'Dimensions': [
                        {
                            'Name': 'Path',
                            'Value': request.path
                        },
                        {
                            'Name': 'Method',
                            'Value': request.method
                        }
                    ]
                }
            ]
        )
        
        if should_log_detail:
            # Log response details
            self.logger.info(
                'Request completed',
                extra={
                    'correlation_id': correlation_id,
                    'status_code': response.status_code,
                    'duration': duration,
                    'response_size': len(response.content)
                }
            )
        
        # Add correlation ID to response headers
        response['X-Correlation-ID'] = correlation_id
        return response

class SecurityHeadersMiddleware:
    """
    Middleware for adding comprehensive security headers with enhanced CSP and HSTS policies.
    """
    
    def __init__(self, get_response: Callable) -> None:
        """
        Initialize middleware with security policy configuration.
        
        Args:
            get_response: Callable to process the request
        """
        self.get_response = get_response
        
        # Configure Content Security Policy
        self.csp_policy = {
            'default-src': ["'self'"],
            'script-src': ["'self'", "'strict-dynamic'"],
            'style-src': ["'self'", "'unsafe-inline'"],
            'img-src': ["'self'", 'data:', 'https:'],
            'font-src': ["'self'"],
            'connect-src': ["'self'", 'https://api.amazonaws.com'],
            'frame-ancestors': ["'none'"],
            'form-action': ["'self'"],
            'base-uri': ["'self'"],
            'object-src': ["'none'"]
        }
        
        # Configure Feature Policy
        self.feature_policy = {
            'camera': "'none'",
            'microphone': "'none'",
            'geolocation': "'none'",
            'payment': "'none'",
            'usb': "'none'"
        }
        
    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        Add comprehensive security headers to response.
        
        Args:
            request: The incoming HTTP request
            
        Returns:
            HttpResponse with security headers
        """
        response = self.get_response(request)
        
        # Generate CSP header
        csp_directives = []
        for directive, sources in self.csp_policy.items():
            csp_directives.append(f"{directive} {' '.join(sources)}")
        
        # Add security headers
        response['Content-Security-Policy'] = '; '.join(csp_directives)
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Add Feature-Policy header
        feature_policy = '; '.join(f"{feature} {value}" 
                                 for feature, value in self.feature_policy.items())
        response['Feature-Policy'] = feature_policy
        
        # Cache security headers
        cache_key = f"security_headers:{request.path}"
        cache_set(cache_key, dict(response.headers), timeout=3600)
        
        return response

class ExceptionHandlerMiddleware:
    """
    Middleware for handling API exceptions with error aggregation and retry logic.
    """
    
    def __init__(self, get_response: Callable) -> None:
        """
        Initialize middleware with error tracking configuration.
        
        Args:
            get_response: Callable to process the request
        """
        self.get_response = get_response
        self.logger = logging.getLogger('error.tracking')
        self.error_counts: Dict[str, int] = {}
        self.retry_limit = getattr(settings, 'ERROR_RETRY_LIMIT', 3)
        
    def process_exception(self, request: HttpRequest, exception: Exception) -> Optional[JsonResponse]:
        """
        Handle exceptions with retry logic and error aggregation.
        
        Args:
            request: The incoming HTTP request
            exception: The raised exception
            
        Returns:
            JsonResponse with error details or None
        """
        # Get correlation ID from request if available
        correlation_id = getattr(request, 'correlation_id', str(uuid.uuid4()))
        
        # Handle API exceptions
        if isinstance(exception, BaseAPIException):
            # Log exception with context
            self.logger.error(
                'API Exception occurred',
                extra={
                    'correlation_id': correlation_id,
                    'error_code': exception.error_code,
                    'path': request.path,
                    'method': request.method
                },
                exc_info=True
            )
            
            # Track error occurrence
            error_key = f"{exception.__class__.__name__}:{request.path}"
            self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
            
            # Check if retry is possible
            if self.error_counts[error_key] <= self.retry_limit:
                # Attempt retry
                try:
                    return self.get_response(request)
                except Exception:
                    pass
            
            # Send error metrics to CloudWatch
            self.send_error_metrics(exception, request.path)
            
            # Return formatted error response
            return JsonResponse(
                exception.detail,
                status=exception.status_code
            )
        
        # Handle unexpected exceptions
        self.logger.critical(
            'Unexpected exception occurred',
            extra={
                'correlation_id': correlation_id,
                'path': request.path,
                'method': request.method
            },
            exc_info=True
        )
        
        return JsonResponse(
            {
                'error_code': f"UNEXPECTED_{uuid.uuid4().hex[:8].upper()}",
                'message': 'An unexpected error occurred',
                'correlation_id': correlation_id
            },
            status=500
        )
    
    def send_error_metrics(self, exception: BaseAPIException, path: str) -> None:
        """
        Send error metrics to CloudWatch.
        
        Args:
            exception: The API exception
            path: Request path
        """
        cloudwatch = boto3.client('cloudwatch', region_name=settings.AWS_REGION)
        cloudwatch.put_metric_data(
            Namespace='TRMS/Errors',
            MetricData=[
                {
                    'MetricName': 'APIException',
                    'Value': 1,
                    'Unit': 'Count',
                    'Dimensions': [
                        {
                            'Name': 'ErrorType',
                            'Value': exception.__class__.__name__
                        },
                        {
                            'Name': 'Path',
                            'Value': path
                        }
                    ]
                }
            ]
        )