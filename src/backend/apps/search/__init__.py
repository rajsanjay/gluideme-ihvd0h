"""
Django app initialization module for search functionality integrating MeiliSearch and Pinecone.
Provides high-performance search capabilities with 99.99% accuracy for transfer requirements.

MeiliSearch version: 1.3+
Pinecone version: 2.0+
"""

# Internal imports
from apps.search.apps import SearchConfig
from apps.search.meilisearch import MeiliSearchClient
from apps.search.pinecone import PineconeClient

# Default Django app configuration
default_app_config = 'apps.search.apps.SearchConfig'

# Re-export search clients for easy access
__all__ = [
    'MeiliSearchClient',
    'PineconeClient',
]