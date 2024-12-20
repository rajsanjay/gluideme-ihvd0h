"""
Django REST Framework views implementing search endpoints for transfer requirements and courses.
Provides optimized search with MeiliSearch and Pinecone integration, caching, and monitoring.

Version: 1.0
"""

# External imports
from rest_framework.views import APIView  # v3.14+
from rest_framework.response import Response  # v3.14+
from rest_framework import status  # v3.14+
from django.core.cache import cache  # v4.2+
from opentelemetry import trace  # v1.12+
from typing import Dict, Any, Optional
import logging
import time

# Internal imports
from apps.search.meilisearch import MeiliSearchClient
from apps.search.pinecone import PineconeClient
from utils.pagination import StandardResultsSetPagination
from utils.exceptions import ValidationError

# Configure logging and tracing
logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

class SearchView(APIView):
    """
    Enhanced search view implementing full-text and vector similarity search
    with caching, monitoring, and comprehensive error handling.
    """
    
    pagination_class = StandardResultsSetPagination
    
    def __init__(self, *args, **kwargs):
        """Initialize search clients and configuration."""
        super().__init__(*args, **kwargs)
        self.meili_client = MeiliSearchClient()
        self.pinecone_client = PineconeClient.get_instance()
        self.paginator = self.pagination_class()
        self.cache_ttl = 300  # 5 minutes cache timeout

    def _validate_search_params(self, params: Dict[str, Any]) -> None:
        """
        Validate search parameters with comprehensive checks.
        
        Args:
            params: Search parameters from request
            
        Raises:
            ValidationError: If parameters are invalid
        """
        # Validate query
        query = params.get('query', '').strip()
        if not query:
            raise ValidationError(
                message="Search query is required",
                validation_errors={'query': 'This field is required'}
            )
        if len(query) < 2:
            raise ValidationError(
                message="Search query too short",
                validation_errors={'query': 'Minimum length is 2 characters'}
            )

        # Validate filters
        filters = params.get('filters', {})
        if not isinstance(filters, dict):
            raise ValidationError(
                message="Invalid filters format",
                validation_errors={'filters': 'Must be a valid object'}
            )

        # Validate pagination
        try:
            page_size = int(params.get('page_size', 20))
            if page_size < 1 or page_size > 100:
                raise ValidationError(
                    message="Invalid page size",
                    validation_errors={'page_size': 'Must be between 1 and 100'}
                )
        except (TypeError, ValueError):
            raise ValidationError(
                message="Invalid page size value",
                validation_errors={'page_size': 'Must be a valid integer'}
            )

    def _generate_cache_key(self, params: Dict[str, Any]) -> str:
        """
        Generate cache key for search results.
        
        Args:
            params: Search parameters
            
        Returns:
            str: Cache key
        """
        key_components = [
            'search',
            params.get('query', ''),
            str(params.get('filters', {})),
            str(params.get('page', 1)),
            str(params.get('page_size', 20))
        ]
        return ':'.join(key_components)

    @tracer.start_as_current_span("search_requirements")
    def post(self, request, *args, **kwargs) -> Response:
        """
        Handle search requests with combined full-text and vector search.
        
        Args:
            request: HTTP request with search parameters
            
        Returns:
            Response: Paginated search results with metadata
        """
        try:
            # Start performance monitoring
            start_time = time.time()
            
            # Validate request parameters
            self._validate_search_params(request.data)
            
            query = request.data.get('query', '').strip()
            filters = request.data.get('filters', {})
            page_size = int(request.data.get('page_size', 20))
            
            # Check cache
            cache_key = self._generate_cache_key(request.data)
            cached_response = cache.get(cache_key)
            if cached_response:
                logger.info(f"Cache hit for query: {query}")
                return Response(cached_response)
            
            # Execute MeiliSearch query
            meili_results = self.meili_client.search_requirements(
                query=query,
                filters=filters,
                limit=page_size
            )
            
            # Execute Pinecone vector search if needed
            if len(meili_results['hits']) < page_size:
                vector_results = self.pinecone_client.query_vectors(
                    query_vector=self._generate_query_vector(query),
                    top_k=page_size - len(meili_results['hits']),
                    filters=filters
                )
                # Merge results ensuring no duplicates
                self._merge_search_results(meili_results, vector_results)
            
            # Format and paginate results
            response_data = {
                'results': meili_results['hits'],
                'total_hits': meili_results['total_hits'],
                'metadata': {
                    'query': query,
                    'filters_applied': filters,
                    'processing_time_ms': int((time.time() - start_time) * 1000),
                    'source': 'combined'
                }
            }
            
            # Cache successful response
            cache.set(cache_key, response_data, timeout=self.cache_ttl)
            
            # Return paginated response
            return self.paginator.get_paginated_response(response_data)
            
        except ValidationError as e:
            logger.warning(f"Search validation error: {str(e)}")
            return Response(
                data=e.detail,
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}", exc_info=True)
            return Response(
                {
                    'error': 'Search operation failed',
                    'detail': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _generate_query_vector(self, query: str) -> list:
        """
        Generate vector embedding for query.
        
        Args:
            query: Search query string
            
        Returns:
            list: Query vector embedding
        """
        # Implementation would depend on the specific embedding model used
        # This is a placeholder for the actual vector generation logic
        pass

    def _merge_search_results(self, text_results: Dict[str, Any], 
                            vector_results: list) -> None:
        """
        Merge full-text and vector search results with deduplication.
        
        Args:
            text_results: MeiliSearch results
            vector_results: Pinecone results
        """
        existing_ids = {hit['id'] for hit in text_results['hits']}
        
        for vector_hit in vector_results:
            if vector_hit['id'] not in existing_ids:
                text_results['hits'].append({
                    'id': vector_hit['id'],
                    'score': vector_hit['score'],
                    'metadata': vector_hit['metadata'],
                    'source': 'vector'
                })
                existing_ids.add(vector_hit['id'])