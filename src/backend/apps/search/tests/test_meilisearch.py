"""
Comprehensive test suite for MeiliSearch integration in the Transfer Requirements Management System.
Validates search functionality, performance requirements, caching behavior, and error handling.

Version: 1.0
"""

import pytest  # v7.0+
from unittest.mock import Mock, patch  # v3.11+
from django.core.cache import cache  # v4.2+
from django.conf import settings  # v4.2+
import time
import json
from decimal import Decimal
from apps.search.meilisearch import MeiliSearchClient
from apps.requirements.models import TransferRequirement

# Test constants
MOCK_REQUIREMENT = {
    'id': '123e4567-e89b-12d3-a456-426614174000',
    'title': 'Computer Science Transfer Requirements',
    'description': 'Requirements for CS transfer',
    'major_code': 'CS',
    'institution_name': 'UC Berkeley',
    'type': 'major',
    'status': 'published',
    'validation_accuracy': 99.99,
    'effective_date': '2023-01-01T00:00:00Z'
}

MOCK_COURSE = {
    'id': '123e4567-e89b-12d3-a456-426614174001',
    'code': 'CS 101',
    'name': 'Introduction to Programming',
    'description': 'Basic programming concepts',
    'credits': Decimal('3.00'),
    'institution_name': 'Community College'
}

@pytest.mark.django_db
class TestMeiliSearchClient:
    """
    Comprehensive test suite for MeiliSearch client implementation.
    Tests search functionality, performance, caching, and error handling.
    """

    def setup_method(self):
        """Initialize test environment with mock responses and cache."""
        self.client = MeiliSearchClient(cache_enabled=True)
        self.mock_cache = cache
        self.mock_cache.clear()

        # Configure mock responses
        self.mock_search_response = {
            'hits': [MOCK_REQUIREMENT],
            'processingTimeMs': 50,
            'query': 'computer science',
            'limit': 20,
            'offset': 0,
            'estimatedTotalHits': 1
        }

        self.mock_course_response = {
            'hits': [MOCK_COURSE],
            'processingTimeMs': 45,
            'query': 'CS 101',
            'limit': 20,
            'offset': 0,
            'estimatedTotalHits': 1
        }

    @patch('apps.search.meilisearch.Client')
    def test_search_requirements(self, mock_client):
        """Test requirement search with pagination and filtering."""
        # Configure mock
        mock_index = Mock()
        mock_index.search.return_value = self.mock_search_response
        mock_client.return_value.index.return_value = mock_index

        # Execute search
        result = self.client.search_requirements(
            query="computer science",
            filters={'institution_id': '123'},
            limit=20,
            offset=0
        )

        # Verify search execution
        mock_index.search.assert_called_once()
        search_params = mock_index.search.call_args[1]['filter']
        assert 'institution_id=123' in search_params

        # Validate response format
        assert 'hits' in result
        assert 'total_hits' in result
        assert 'processing_time_ms' in result
        assert 'pagination' in result

        # Verify cache behavior
        cache_key = self.client._generate_cache_key(
            'requirements',
            'computer science',
            {'institution_id': '123'}
        )
        assert self.mock_cache.get(cache_key) is not None

    @patch('apps.search.meilisearch.Client')
    def test_search_courses(self, mock_client):
        """Test course search with metadata validation."""
        # Configure mock
        mock_index = Mock()
        mock_index.search.return_value = self.mock_course_response
        mock_client.return_value.index.return_value = mock_index

        # Execute search
        result = self.client.search_requirements(
            query="CS 101",
            filters={'credits': 3},
            limit=20,
            offset=0
        )

        # Verify search parameters
        mock_index.search.assert_called_once()
        assert result['hits'][0]['code'] == 'CS 101'
        assert Decimal(result['hits'][0]['credits']) == Decimal('3.00')

    @patch('apps.search.meilisearch.Client')
    def test_search_performance(self, mock_client):
        """Validate search latency requirements."""
        # Configure mock
        mock_index = Mock()
        mock_index.search.return_value = self.mock_search_response
        mock_client.return_value.index.return_value = mock_index

        # Execute search and measure time
        start_time = time.time()
        self.client.search_requirements(query="computer science")
        end_time = time.time()

        # Verify performance requirement (200ms)
        search_time = (end_time - start_time) * 1000
        assert search_time < 200, f"Search took {search_time}ms, exceeding 200ms requirement"

    @patch('apps.search.meilisearch.Client')
    def test_update_requirement_index(self, mock_client):
        """Test atomic index updates and versioning."""
        # Create test requirement
        requirement = Mock(spec=TransferRequirement)
        requirement.id = MOCK_REQUIREMENT['id']
        requirement.title = MOCK_REQUIREMENT['title']
        requirement.description = MOCK_REQUIREMENT['description']
        requirement.major_code = MOCK_REQUIREMENT['major_code']
        requirement.validation_accuracy = MOCK_REQUIREMENT['validation_accuracy']

        # Configure mock
        mock_index = Mock()
        mock_client.return_value.index.return_value = mock_index

        # Update index
        self.client.update_requirement_index(requirement)

        # Verify index update
        mock_index.add_documents.assert_called_once()
        added_doc = mock_index.add_documents.call_args[0][0][0]
        assert added_doc['id'] == str(requirement.id)
        assert added_doc['title'] == requirement.title
        assert added_doc['validation_accuracy'] == float(requirement.validation_accuracy)

    @patch('apps.search.meilisearch.Client')
    def test_error_handling(self, mock_client):
        """Verify error handling and timeout scenarios."""
        # Configure mock to raise timeout
        mock_index = Mock()
        mock_index.search.side_effect = Exception("Search timeout")
        mock_client.return_value.index.return_value = mock_index

        # Test error handling
        with pytest.raises(Exception) as exc_info:
            self.client.search_requirements(query="test")
        assert "Search timeout" in str(exc_info.value)

    @patch('apps.search.meilisearch.Client')
    def test_cache_invalidation(self, mock_client):
        """Test cache invalidation on updates."""
        # Configure mock
        mock_index = Mock()
        mock_index.search.return_value = self.mock_search_response
        mock_client.return_value.index.return_value = mock_index

        # Execute search to populate cache
        query = "computer science"
        self.client.search_requirements(query=query)
        
        # Verify cache hit
        cache_key = self.client._generate_cache_key('requirements', query, {})
        assert self.mock_cache.get(cache_key) is not None

        # Update requirement
        requirement = Mock(spec=TransferRequirement)
        requirement.id = MOCK_REQUIREMENT['id']
        self.client.update_requirement_index(requirement)

        # Verify cache invalidation
        assert self.mock_cache.get(cache_key) is None

def pytest_configure(config):
    """Configure test environment and mock settings."""
    settings.MEILISEARCH_HOST = 'http://localhost:7700'
    settings.MEILISEARCH_API_KEY = 'test_key'