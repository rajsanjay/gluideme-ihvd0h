"""
URL routing configuration for the search application.
Implements versioned endpoints for full-text search, autocomplete, and similarity search.

Version: 1.0
"""

# Django v4.2+
from django.urls import path

# Internal imports
from apps.search.views import (
    SearchView,
    AutocompleteView,
    SimilaritySearchView
)

# Define app namespace for URL reversing
app_name = 'search'

# URL patterns with versioning and format support
urlpatterns = [
    # Full-text and combined search endpoint
    path(
        'api/v1/search/',
        SearchView.as_view(),
        name='search'
    ),
    
    # Real-time autocomplete suggestions endpoint
    path(
        'api/v1/search/autocomplete/',
        AutocompleteView.as_view(),
        name='autocomplete'
    ),
    
    # Vector similarity search endpoint
    path(
        'api/v1/search/similar/',
        SimilaritySearchView.as_view(),
        name='similarity'
    )
]