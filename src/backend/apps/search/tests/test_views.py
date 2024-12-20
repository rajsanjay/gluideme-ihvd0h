"""
Comprehensive test suite for search functionality including full-text search, 
autocomplete, and vector similarity search with performance validation.

Version: 1.0
"""

# External imports
from rest_framework.test import APITestCase  # v3.14+
from unittest.mock import patch, MagicMock  # v3.14+
from rest_framework import status  # v3.14+
from django.urls import reverse  # v4.2+
from freezegun import freeze_time  # v1.2+
import time
import json

# Internal imports
from apps.search.views import SearchView, AutocompleteView, SimilaritySearchView
from apps.search.meilisearch import MeiliSearchClient
from apps.search.pinecone import PineconeClient

class SearchViewTests(APITestCase):
    """Test suite for main search functionality with performance validation."""

    maxDiff = None

    def setUp(self):
        """Configure test environment before each test."""
        self.search_url = reverse('search-requirements')
        self.meili_mock = patch('apps.search.views.MeiliSearchClient').start()
        self.pinecone_mock = patch('apps.search.views.PineconeClient').start()
        
        # Configure test data
        self.test_requirements = {
            'hits': [
                {
                    'id': '1',
                    'title': 'Computer Science Transfer Requirements',
                    'institution_name': 'UC Berkeley',
                    'major_code': 'CS',
                    'score': 0.95
                },
                {
                    'id': '2',
                    'title': 'Computer Engineering Requirements',
                    'institution_name': 'UCLA',
                    'major_code': 'CE',
                    'score': 0.85
                }
            ],
            'total_hits': 2,
            'processing_time_ms': 50
        }

        # Configure mock responses
        self.meili_mock.return_value.search_requirements.return_value = self.test_requirements
        self.pinecone_mock.get_instance.return_value.query_vectors.return_value = []

        # Configure Redis mock
        self.redis_mock = patch('django.core.cache.cache').start()
        self.redis_mock.get.return_value = None

    def tearDown(self):
        """Clean up test environment."""
        patch.stopall()

    def test_search_requirements_success(self):
        """Test successful requirements search with performance validation."""
        search_data = {
            'query': 'computer science',
            'filters': {'institution_type': 'university'},
            'page_size': 20
        }

        # Measure performance
        start_time = time.time()
        response = self.client.post(self.search_url, search_data, format='json')
        response_time = time.time() - start_time

        # Validate response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 2)

        # Validate performance requirement (<200ms)
        self.assertLess(response_time, 0.2, "Search response time exceeds 200ms requirement")

        # Validate response structure
        self.assertIn('metadata', response.data)
        self.assertEqual(response.data['metadata']['query'], 'computer science')
        self.assertEqual(response.data['metadata']['filters_applied'], 
                        {'institution_type': 'university'})

        # Validate search was called with correct parameters
        self.meili_mock.return_value.search_requirements.assert_called_once_with(
            query='computer science',
            filters={'institution_type': 'university'},
            limit=20
        )

    def test_search_with_institution_filter(self):
        """Test search with institution filtering."""
        search_data = {
            'query': 'biology',
            'filters': {
                'institution_id': 'uc-berkeley',
                'major_code': 'BIO'
            }
        }

        response = self.client.post(self.search_url, search_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.meili_mock.return_value.search_requirements.assert_called_once_with(
            query='biology',
            filters={
                'institution_id': 'uc-berkeley',
                'major_code': 'BIO'
            },
            limit=20
        )

    def test_search_validation_error(self):
        """Test search with invalid parameters."""
        invalid_data = {
            'query': '',  # Empty query
            'filters': 'invalid'  # Invalid filters format
        }

        response = self.client.post(self.search_url, invalid_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('validation_errors', response.data)

    @freeze_time("2023-01-01 12:00:00")
    def test_search_cache_behavior(self):
        """Test search result caching."""
        search_data = {
            'query': 'engineering',
            'filters': {'institution_type': 'university'}
        }

        # First request - should miss cache
        response1 = self.client.post(self.search_url, search_data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.meili_mock.return_value.search_requirements.assert_called_once()

        # Configure cache hit for second request
        self.redis_mock.get.return_value = json.dumps(response1.data)

        # Second request - should hit cache
        response2 = self.client.post(self.search_url, search_data, format='json')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Verify cache was used
        self.assertEqual(response1.data, response2.data)
        self.assertEqual(self.meili_mock.return_value.search_requirements.call_count, 1)

class AutocompleteViewTests(APITestCase):
    """Test suite for autocomplete functionality with performance validation."""

    def setUp(self):
        """Configure test environment."""
        self.autocomplete_url = reverse('search-autocomplete')
        self.meili_mock = patch('apps.search.views.MeiliSearchClient').start()
        
        # Configure test suggestions
        self.test_suggestions = [
            'Computer Science',
            'Computer Engineering',
            'Computer Information Systems'
        ]
        self.meili_mock.return_value.get_suggestions.return_value = self.test_suggestions

    def test_get_suggestions_performance(self):
        """Test suggestion retrieval with performance validation."""
        # Measure performance
        start_time = time.time()
        response = self.client.get(
            self.autocomplete_url,
            {'query': 'comp', 'limit': 5}
        )
        response_time = time.time() - start_time

        # Validate response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['suggestions']), 3)
        self.assertEqual(response.data['suggestions'], self.test_suggestions)

        # Validate performance requirement (<100ms)
        self.assertLess(response_time, 0.1, "Autocomplete response time exceeds 100ms requirement")

        # Verify correct parameters
        self.meili_mock.return_value.get_suggestions.assert_called_once_with(
            'comp',
            limit=5
        )

class SimilaritySearchViewTests(APITestCase):
    """Test suite for vector similarity search with threshold validation."""

    def setUp(self):
        """Configure test environment."""
        self.similarity_url = reverse('search-similarity')
        self.pinecone_mock = patch('apps.search.views.PineconeClient').start()
        
        # Configure test vectors
        self.test_vectors = [
            {
                'id': '1',
                'score': 0.92,
                'metadata': {
                    'title': 'Computer Science Requirements',
                    'institution': 'UC Berkeley'
                }
            },
            {
                'id': '2',
                'score': 0.85,
                'metadata': {
                    'title': 'Software Engineering Requirements',
                    'institution': 'UCLA'
                }
            }
        ]
        self.pinecone_mock.get_instance.return_value.query_vectors.return_value = self.test_vectors

    def test_similarity_search_threshold(self):
        """Test similarity search with threshold validation."""
        search_data = {
            'query_vector': [0.1] * 512,  # Example vector
            'threshold': 0.8,
            'top_k': 5
        }

        response = self.client.post(self.similarity_url, search_data, format='json')

        # Validate response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

        # Validate similarity scores
        for result in response.data['results']:
            self.assertGreaterEqual(
                result['score'],
                0.8,
                "Result score below similarity threshold"
            )

        # Verify correct parameters
        self.pinecone_mock.get_instance.return_value.query_vectors.assert_called_once_with(
            query_vector=search_data['query_vector'],
            top_k=search_data['top_k'],
            filters=None
        )