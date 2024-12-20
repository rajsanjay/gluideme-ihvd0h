"""
MeiliSearch client implementation for the Transfer Requirements Management System.
Provides optimized full-text search with caching, validation, and error handling.

Version: 1.0
"""

from meilisearch import Client  # v1.3+
from django.conf import settings
from django.core.cache import cache
import hashlib
import json
import logging
from typing import Dict, List, Optional, Any
from apps.requirements.models import TransferRequirement

logger = logging.getLogger(__name__)

# Global constants for search configuration
MEILI_HOST = settings.MEILISEARCH_HOST
MEILI_KEY = settings.MEILISEARCH_API_KEY
REQUIREMENTS_INDEX = 'requirements'
COURSES_INDEX = 'courses'
CACHE_TTL = 300  # 5 minutes
MAX_SEARCH_RESULTS = 1000
DEFAULT_PAGE_SIZE = 20
SEARCH_TIMEOUT = 2.0  # 2 seconds timeout

class MeiliSearchClient:
    """
    Enhanced MeiliSearch client with caching, validation, and error handling.
    Implements comprehensive search functionality for transfer requirements and courses.
    """

    def __init__(self, cache_enabled: bool = True, timeout: float = SEARCH_TIMEOUT) -> None:
        """
        Initialize MeiliSearch client with enhanced configuration.

        Args:
            cache_enabled: Enable result caching
            timeout: Search operation timeout in seconds
        """
        try:
            # Initialize client with configuration
            self.client = Client(MEILI_HOST, MEILI_KEY, timeout=timeout)
            self.requirements_index = self.client.index(REQUIREMENTS_INDEX)
            self.courses_index = self.client.index(COURSES_INDEX)
            self.cache_enabled = cache_enabled
            self.timeout = timeout

            # Configure requirements index
            self.requirements_index.update_settings({
                'searchableAttributes': [
                    'title',
                    'description',
                    'major_code',
                    'institution_name',
                    'metadata'
                ],
                'filterableAttributes': [
                    'institution_id',
                    'major_code',
                    'status',
                    'type'
                ],
                'sortableAttributes': [
                    'effective_date',
                    'validation_accuracy'
                ],
                'rankingRules': [
                    'words',
                    'typo',
                    'proximity',
                    'attribute',
                    'sort',
                    'exactness',
                    'validation_accuracy:desc'
                ]
            })

            # Configure courses index
            self.courses_index.update_settings({
                'searchableAttributes': [
                    'code',
                    'name',
                    'description',
                    'institution_name'
                ],
                'filterableAttributes': [
                    'institution_id',
                    'status',
                    'credits'
                ],
                'sortableAttributes': [
                    'code',
                    'credits'
                ]
            })

            logger.info("MeiliSearch client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize MeiliSearch client: {str(e)}", exc_info=True)
            raise

    def _generate_cache_key(self, index: str, query: str, filters: Dict) -> str:
        """
        Generate secure cache key for search results.

        Args:
            index: Index name
            query: Search query
            filters: Search filters

        Returns:
            str: Secure cache key
        """
        key_data = {
            'index': index,
            'query': query,
            'filters': sorted(filters.items())
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return f"meili_search:{hashlib.sha256(key_string.encode()).hexdigest()}"

    def _validate_search_params(self, query: str, filters: Dict, 
                              limit: int, offset: int) -> None:
        """
        Validate search parameters with comprehensive checks.

        Args:
            query: Search query
            filters: Search filters
            limit: Result limit
            offset: Result offset

        Raises:
            ValueError: If parameters are invalid
        """
        if not isinstance(query, str):
            raise ValueError("Query must be a string")

        if not isinstance(filters, dict):
            raise ValueError("Filters must be a dictionary")

        if not 0 < limit <= MAX_SEARCH_RESULTS:
            raise ValueError(f"Limit must be between 1 and {MAX_SEARCH_RESULTS}")

        if offset < 0:
            raise ValueError("Offset must be non-negative")

    def search_requirements(self, query: str, filters: Dict = None, 
                          limit: int = DEFAULT_PAGE_SIZE, 
                          offset: int = 0,
                          institution_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Search transfer requirements with enhanced filtering and caching.

        Args:
            query: Search query string
            filters: Optional search filters
            limit: Maximum results per page
            offset: Result offset for pagination
            institution_id: Optional institution filter

        Returns:
            Dict: Search results with metadata
        """
        try:
            # Validate parameters
            filters = filters or {}
            self._validate_search_params(query, filters, limit, offset)

            # Add institution filter if provided
            if institution_id:
                filters['institution_id'] = institution_id

            # Check cache
            cache_key = self._generate_cache_key(REQUIREMENTS_INDEX, query, filters)
            if self.cache_enabled:
                cached_results = cache.get(cache_key)
                if cached_results:
                    logger.debug(f"Cache hit for query: {query}")
                    return cached_results

            # Execute search
            search_results = self.requirements_index.search(
                query,
                {
                    'filter': [f"{k}={v}" for k, v in filters.items()],
                    'limit': limit,
                    'offset': offset,
                    'attributesToRetrieve': [
                        'id',
                        'title',
                        'description',
                        'major_code',
                        'institution_name',
                        'type',
                        'status',
                        'effective_date',
                        'validation_accuracy'
                    ]
                }
            )

            # Validate results
            hits = []
            for hit in search_results['hits']:
                requirement = TransferRequirement.objects.get(pk=hit['id'])
                is_active, reasons = requirement.is_active()
                if is_active:
                    hits.append(hit)

            # Format response
            response = {
                'hits': hits,
                'total_hits': len(hits),
                'processing_time_ms': search_results['processingTimeMs'],
                'query': query,
                'filters': filters,
                'pagination': {
                    'limit': limit,
                    'offset': offset,
                    'total_pages': (len(hits) + limit - 1) // limit
                }
            }

            # Cache results
            if self.cache_enabled:
                cache.set(cache_key, response, timeout=CACHE_TTL)

            logger.info(
                f"Search completed - query: {query}, hits: {len(hits)}, "
                f"time: {search_results['processingTimeMs']}ms"
            )
            return response

        except Exception as e:
            logger.error(f"Search failed - query: {query}, error: {str(e)}", exc_info=True)
            raise

    def update_requirement_index(self, requirement: TransferRequirement) -> None:
        """
        Update requirement in search index with validation.

        Args:
            requirement: TransferRequirement instance to index
        """
        try:
            # Prepare document
            document = {
                'id': str(requirement.id),
                'title': requirement.title,
                'description': requirement.description,
                'major_code': requirement.major_code,
                'institution_id': str(requirement.source_institution.id),
                'institution_name': requirement.source_institution.name,
                'type': requirement.type,
                'status': requirement.status,
                'effective_date': requirement.effective_date.isoformat(),
                'validation_accuracy': float(requirement.validation_accuracy),
                'metadata': requirement.metadata
            }

            # Add to index
            self.requirements_index.add_documents([document])
            logger.info(f"Indexed requirement: {requirement.id}")

        except Exception as e:
            logger.error(
                f"Failed to index requirement {requirement.id}: {str(e)}", 
                exc_info=True
            )
            raise

    def delete_requirement(self, requirement_id: str) -> None:
        """
        Delete requirement from search index.

        Args:
            requirement_id: ID of requirement to delete
        """
        try:
            self.requirements_index.delete_document(requirement_id)
            logger.info(f"Deleted requirement from index: {requirement_id}")
        except Exception as e:
            logger.error(
                f"Failed to delete requirement {requirement_id}: {str(e)}", 
                exc_info=True
            )
            raise

    def get_suggestions(self, query: str, limit: int = 5) -> List[str]:
        """
        Get search suggestions for partial queries.

        Args:
            query: Partial search query
            limit: Maximum number of suggestions

        Returns:
            List[str]: Search suggestions
        """
        try:
            results = self.requirements_index.search(
                query,
                {
                    'limit': limit,
                    'attributesToRetrieve': ['title'],
                    'attributesToHighlight': ['title']
                }
            )
            return [hit['title'] for hit in results['hits']]
        except Exception as e:
            logger.error(f"Failed to get suggestions: {str(e)}", exc_info=True)
            return []