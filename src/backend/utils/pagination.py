"""
Custom pagination classes for the Transfer Requirements Management System.
Implements high-performance page and cursor-based pagination with caching support.

Version: 1.0
"""

# rest_framework v3.14+
from rest_framework import pagination
from rest_framework.response import Response

# Standard library imports
import base64
import hmac
import hashlib
import json
import time
from typing import Dict, List, Optional, Any

# Internal imports
from utils.exceptions import ValidationError

class StandardPagination(pagination.PageNumberPagination):
    """
    Standard page number-based pagination optimized for general API endpoints.
    Implements caching and performance optimizations for improved response times.
    """
    
    page_size = 20  # Default items per page
    max_page_size = 100  # Maximum allowed items per page
    page_size_query_param = 'page_size'
    page_query_param = 'page'
    last_page_strings = ('last', 'end')
    
    def __init__(self) -> None:
        """Initialize pagination with performance optimizations."""
        super().__init__()
        self._page_cache: Dict[str, Dict] = {}
        self._cache_timeout = 300  # 5 minutes cache timeout
    
    def get_paginated_response(self, data: List[Any]) -> Response:
        """
        Return paginated response with comprehensive metadata.
        
        Args:
            data: List of items for current page
            
        Returns:
            Response: Formatted response with pagination metadata
        """
        count = self.page.paginator.count
        current_page = self.page.number
        total_pages = self.page.paginator.num_pages
        
        # Calculate page statistics
        start_index = (current_page - 1) * self.page_size + 1
        end_index = min(start_index + self.page_size - 1, count)
        
        # Generate cache key
        cache_key = f"{count}:{current_page}:{self.page_size}"
        
        # Check cache for existing metadata
        if cache_key in self._page_cache:
            cached = self._page_cache[cache_key]
            if time.time() - cached['timestamp'] < self._cache_timeout:
                cached['results'] = data
                return Response(cached)
        
        # Construct response with metadata
        response_data = {
            'count': count,
            'total_pages': total_pages,
            'current_page': current_page,
            'page_size': self.page_size,
            'start_index': start_index,
            'end_index': end_index,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
            'timestamp': time.time()
        }
        
        # Cache response metadata
        self._page_cache[cache_key] = response_data
        
        # Clean old cache entries
        self._clean_cache()
        
        return Response(response_data)
    
    def validate_page_size(self, requested_size: int) -> int:
        """
        Validate and normalize requested page size.
        
        Args:
            requested_size: Requested page size
            
        Returns:
            int: Validated page size
            
        Raises:
            ValidationError: If page size is invalid
        """
        try:
            page_size = int(requested_size)
            if page_size < 1:
                raise ValidationError(
                    message="Page size must be greater than 0",
                    validation_errors={'page_size': 'Minimum value is 1'}
                )
            if page_size > self.max_page_size:
                return self.max_page_size
            return page_size
        except (TypeError, ValueError):
            raise ValidationError(
                message="Invalid page size value",
                validation_errors={'page_size': 'Must be a valid integer'}
            )
    
    def _clean_cache(self) -> None:
        """Remove expired cache entries to prevent memory growth."""
        current_time = time.time()
        expired_keys = [
            key for key, value in self._page_cache.items()
            if current_time - value['timestamp'] > self._cache_timeout
        ]
        for key in expired_keys:
            del self._page_cache[key]


class CursorPagination(pagination.CursorPagination):
    """
    Cursor-based pagination for high-performance scrolling through large datasets.
    Implements secure cursor signing and caching for optimal performance.
    """
    
    page_size = 50  # Optimized for large datasets
    max_page_size = 200
    cursor_query_param = 'cursor'
    ordering = '-created_at'  # Default ordering field
    
    def __init__(self) -> None:
        """Initialize cursor pagination with security and caching."""
        super().__init__()
        self._cursor_secret = hashlib.sha256().hexdigest()  # Secure cursor signing
        self._cursor_cache: Dict[str, Dict] = {}
        self._cache_timeout = 300
    
    def encode_cursor(self, cursor_value: Dict) -> str:
        """
        Encode and sign cursor value for secure pagination.
        
        Args:
            cursor_value: Dictionary containing cursor data
            
        Returns:
            str: Signed and encoded cursor string
        """
        if not isinstance(cursor_value, dict):
            raise ValidationError(
                message="Invalid cursor value",
                validation_errors={'cursor': 'Must be a valid cursor object'}
            )
        
        # Add timestamp for security
        cursor_value['timestamp'] = int(time.time())
        
        # Convert to string and encode
        cursor_string = json.dumps(cursor_value, sort_keys=True)
        cursor_bytes = cursor_string.encode()
        
        # Generate signature
        signature = hmac.new(
            self._cursor_secret.encode(),
            cursor_bytes,
            hashlib.sha256
        ).hexdigest()
        
        # Combine cursor and signature
        combined = f"{cursor_string}|{signature}"
        encoded = base64.urlsafe_b64encode(combined.encode()).decode()
        
        # Cache encoded cursor
        self._cursor_cache[encoded] = {
            'value': cursor_value,
            'timestamp': time.time()
        }
        
        return encoded
    
    def decode_cursor(self, encoded_cursor: str) -> Dict:
        """
        Decode and verify cursor value from request.
        
        Args:
            encoded_cursor: Encoded cursor string
            
        Returns:
            dict: Verified cursor value
            
        Raises:
            ValidationError: If cursor is invalid or tampered
        """
        # Check cache first
        if encoded_cursor in self._cursor_cache:
            cached = self._cursor_cache[encoded_cursor]
            if time.time() - cached['timestamp'] < self._cache_timeout:
                return cached['value']
        
        try:
            # Decode cursor
            decoded = base64.urlsafe_b64decode(encoded_cursor.encode()).decode()
            cursor_string, signature = decoded.split('|')
            
            # Verify signature
            expected_signature = hmac.new(
                self._cursor_secret.encode(),
                cursor_string.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                raise ValidationError(
                    message="Invalid cursor signature",
                    validation_errors={'cursor': 'Cursor has been tampered with'}
                )
            
            # Parse cursor value
            cursor_value = json.loads(cursor_string)
            
            # Verify timestamp
            if time.time() - cursor_value['timestamp'] > 3600:  # 1 hour expiry
                raise ValidationError(
                    message="Cursor has expired",
                    validation_errors={'cursor': 'Please refresh the page'}
                )
            
            # Cache decoded value
            self._cursor_cache[encoded_cursor] = {
                'value': cursor_value,
                'timestamp': time.time()
            }
            
            return cursor_value
            
        except (ValueError, json.JSONDecodeError, KeyError):
            raise ValidationError(
                message="Invalid cursor format",
                validation_errors={'cursor': 'Cursor format is invalid'}
            )
    
    def get_paginated_response(self, data: List[Any]) -> Response:
        """
        Return cursor-paginated response with navigation links.
        
        Args:
            data: List of items for current page
            
        Returns:
            Response: Formatted response with cursor pagination metadata
        """
        next_cursor = self.get_next_link()
        previous_cursor = self.get_previous_link()
        
        response_data = {
            'next': next_cursor,
            'previous': previous_cursor,
            'results': data,
            'page_size': self.page_size,
            'count': len(data),
            'has_next': bool(next_cursor),
            'has_previous': bool(previous_cursor),
            'performance_metrics': {
                'response_time': time.time(),
                'cached': False
            }
        }
        
        return Response(response_data)