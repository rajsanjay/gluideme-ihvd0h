"""
Test package initialization file for the search application's test suite.
Configures test environment and common test utilities for MeiliSearch and Pinecone integration testing.

Version: 1.0
"""

# External imports
import pytest  # v7.0+
from unittest.mock import Mock, patch  # v3.11+
import time
from typing import Dict, Any, List, Optional

# Internal imports
from apps.search.meilisearch import MeiliSearchClient
from apps.search.pinecone import PineconeClient

# Test configuration constants
TEST_REQUIREMENTS_INDEX = 'test-requirements'
TEST_COURSES_INDEX = 'test-courses'
SEARCH_LATENCY_THRESHOLD = 0.2  # 200ms per technical spec
WARM_UP_CYCLES = 3  # Number of warm-up cycles for performance testing

def pytest_configure(config: pytest.Config) -> None:
    """
    Configure test environment for search tests with comprehensive setup of mock clients,
    test indexes, and performance monitoring.

    Args:
        config: pytest configuration object
    """
    # Register custom markers
    config.addinivalue_line(
        "markers",
        "search_integration: mark test as search integration test"
    )
    config.addinivalue_line(
        "markers",
        "performance: mark test as performance test"
    )

    # Configure test environment variables
    config.setenv('MEILISEARCH_INDEX', TEST_REQUIREMENTS_INDEX)
    config.setenv('PINECONE_INDEX', TEST_COURSES_INDEX)

class SearchTestCase:
    """
    Comprehensive base test case class for search functionality tests with built-in
    performance monitoring and test isolation.
    """

    def __init__(self):
        """Initialize test case with mock search clients and performance monitoring."""
        self.meili_client = None
        self.pinecone_client = None
        self.performance_metrics = {
            'search_latency': [],
            'index_operations': [],
            'cache_hits': 0,
            'cache_misses': 0
        }
        self.test_data = {}

    def setUp(self) -> None:
        """
        Set up test environment before each test with proper isolation.
        Initializes mock clients and test data.
        """
        # Initialize mock MeiliSearch client
        self.meili_client = Mock(spec=MeiliSearchClient)
        self.meili_client.requirements_index = TEST_REQUIREMENTS_INDEX
        self.meili_client.courses_index = TEST_COURSES_INDEX

        # Initialize mock Pinecone client
        self.pinecone_client = Mock(spec=PineconeClient)
        self.pinecone_client.get_instance.return_value = self.pinecone_client

        # Reset performance metrics
        self.performance_metrics = {
            'search_latency': [],
            'index_operations': [],
            'cache_hits': 0,
            'cache_misses': 0
        }

        # Initialize test data
        self._initialize_test_data()

        # Perform warm-up cycles
        self._perform_warm_up()

    def tearDown(self) -> None:
        """
        Clean up test environment after each test with comprehensive cleanup.
        Clears test data and resets mock states.
        """
        # Clear test indexes
        if self.meili_client:
            self.meili_client.delete_index(TEST_REQUIREMENTS_INDEX)
            self.meili_client.delete_index(TEST_COURSES_INDEX)

        # Clear Pinecone test data
        if self.pinecone_client:
            self.pinecone_client.clear_index()

        # Store performance metrics if needed
        self._store_performance_metrics()

        # Reset mock states
        self.meili_client.reset_mock()
        self.pinecone_client.reset_mock()

        # Clear test data
        self.test_data.clear()

    def measure_search_performance(self, search_func: callable, *args) -> tuple:
        """
        Utility method to measure and validate search performance.

        Args:
            search_func: Search function to measure
            args: Arguments for search function

        Returns:
            tuple: Search results and timing metrics
        """
        start_time = time.time()
        results = search_func(*args)
        execution_time = time.time() - start_time

        # Validate against performance requirements
        assert execution_time <= SEARCH_LATENCY_THRESHOLD, (
            f"Search latency {execution_time:.3f}s exceeded threshold "
            f"of {SEARCH_LATENCY_THRESHOLD}s"
        )

        # Store metrics
        self.performance_metrics['search_latency'].append(execution_time)

        return results, execution_time

    def _initialize_test_data(self) -> None:
        """Initialize test data for search operations."""
        self.test_data = {
            'requirements': [
                {
                    'id': 'req1',
                    'title': 'Computer Science Transfer Requirements',
                    'description': 'Transfer requirements for CS program',
                    'major_code': 'CS',
                    'institution_name': 'Test University'
                },
                # Add more test requirements as needed
            ],
            'courses': [
                {
                    'id': 'course1',
                    'code': 'CS101',
                    'name': 'Introduction to Programming',
                    'description': 'Basic programming concepts',
                    'institution_name': 'Test College'
                },
                # Add more test courses as needed
            ]
        }

    def _perform_warm_up(self) -> None:
        """
        Perform warm-up cycles to stabilize performance measurements.
        Executes sample searches to prime caches and connections.
        """
        for _ in range(WARM_UP_CYCLES):
            # Warm up MeiliSearch
            self.meili_client.search_requirements(
                query="test",
                filters={'institution_id': 'test'}
            )
            self.meili_client.search_courses(
                query="test",
                filters={'institution_id': 'test'}
            )

            # Warm up Pinecone
            self.pinecone_client.query_vectors(
                query_vector=[0.1] * 512,  # Sample vector
                top_k=5
            )

    def _store_performance_metrics(self) -> None:
        """Store performance metrics for analysis."""
        if self.performance_metrics['search_latency']:
            avg_latency = sum(self.performance_metrics['search_latency']) / len(
                self.performance_metrics['search_latency']
            )
            print(f"\nAverage search latency: {avg_latency:.3f}s")
            print(f"Cache hits: {self.performance_metrics['cache_hits']}")
            print(f"Cache misses: {self.performance_metrics['cache_misses']}")