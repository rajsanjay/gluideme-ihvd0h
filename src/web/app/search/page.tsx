"use client";

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { cn } from 'class-variance-authority'; // v0.7.0
import SearchForm from '../../components/search/search-form';
import ResultsGrid from '../../components/search/results-grid';
import SearchFilters from '../../components/search/filters';
import { useSearch } from '../../hooks/useSearch';
import type { SearchType, SearchFilters as SearchFilterType } from '../../types/search';
import ErrorBoundary from '../../components/common/error-boundary';
import { Toast } from '../../components/common/toast';

/**
 * SearchPage component implementing comprehensive search functionality
 * with dual search engine support (MeiliSearch and Pinecone)
 */
const SearchPage: React.FC = () => {
  // Initialize search hook with configuration
  const {
    searchState,
    searchResults,
    totalResults,
    isLoading,
    error,
    handleQueryChange,
    handleTypeChange,
    handleFiltersChange,
    handlePageChange,
    paginationParams
  } = useSearch({
    initialQuery: '',
    initialType: 'requirements',
    initialFilters: {
      institutionTypes: [],
      majorCategories: [],
      effectiveDate: { startDate: '', endDate: '' },
      status: 'active'
    },
    enableHistory: true,
    cacheTimeout: 5 * 60 * 1000 // 5 minutes cache
  });

  // Refs for accessibility and analytics
  const searchContainerRef = useRef<HTMLDivElement>(null);
  const announcementRef = useRef<HTMLDivElement>(null);
  const analyticsTimeoutRef = useRef<NodeJS.Timeout>();

  // View mode state for results display
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  /**
   * Handle search form submission with dual engine support
   */
  const handleSearch = useCallback(async (
    query: string,
    type: SearchType,
    filters: SearchFilterType
  ) => {
    try {
      await handleQueryChange(query);
      handleTypeChange(type);
      handleFiltersChange(filters);

      // Announce search status to screen readers
      if (announcementRef.current) {
        announcementRef.current.textContent = isLoading
          ? 'Searching...'
          : `Found ${totalResults} results`;
      }

      // Track search analytics
      if (analyticsTimeoutRef.current) {
        clearTimeout(analyticsTimeoutRef.current);
      }
      analyticsTimeoutRef.current = setTimeout(() => {
        // Implementation would integrate with your analytics system
        console.log('Search analytics:', {
          query,
          type,
          filters,
          timestamp: new Date()
        });
      }, 1000);

    } catch (err) {
      console.error('Search error:', err);
      Toast.show({
        type: 'error',
        title: 'Search Error',
        message: 'Failed to perform search. Please try again.',
        duration: 5000
      });
    }
  }, [handleQueryChange, handleTypeChange, handleFiltersChange, isLoading, totalResults]);

  /**
   * Handle result selection
   */
  const handleResultClick = useCallback((result) => {
    // Implementation would handle navigation to result details
    console.log('Selected result:', result);
  }, []);

  /**
   * Handle filter changes with validation
   */
  const handleFilterChange = useCallback((newFilters: SearchFilterType) => {
    handleFiltersChange(newFilters);
  }, [handleFiltersChange]);

  /**
   * Handle view mode toggle
   */
  const handleViewModeChange = useCallback((mode: 'grid' | 'list') => {
    setViewMode(mode);
    // Announce view mode change to screen readers
    if (announcementRef.current) {
      announcementRef.current.textContent = `View changed to ${mode} mode`;
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (analyticsTimeoutRef.current) {
        clearTimeout(analyticsTimeoutRef.current);
      }
    };
  }, []);

  return (
    <ErrorBoundary
      fallback={
        <div className="p-4 text-red-600" role="alert">
          An error occurred while loading the search page
        </div>
      }
    >
      <div
        ref={searchContainerRef}
        className="container mx-auto px-4 py-8 space-y-8"
        role="main"
        aria-label="Search page"
      >
        {/* Search Form */}
        <SearchForm
          onSearch={handleSearch}
          initialQuery={searchState.query}
          initialType={searchState.type}
          initialFilters={searchState.filters}
          analyticsEnabled={true}
          className="mb-8"
        />

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Filters Panel */}
          <aside className="lg:col-span-1">
            <SearchFilters
              filters={searchState.filters}
              onChange={handleFilterChange}
              className="sticky top-4"
            />
          </aside>

          {/* Results Section */}
          <main className="lg:col-span-3">
            {/* Results Controls */}
            <div className="flex justify-between items-center mb-4">
              <div className="text-sm text-gray-600">
                {totalResults > 0 && !isLoading ? (
                  <span>{`${totalResults} results found`}</span>
                ) : null}
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => handleViewModeChange('grid')}
                  className={cn(
                    'p-2 rounded-md',
                    viewMode === 'grid' && 'bg-primary-100'
                  )}
                  aria-pressed={viewMode === 'grid'}
                  aria-label="Grid view"
                >
                  <span className="sr-only">Grid view</span>
                  {/* Grid icon */}
                </button>
                <button
                  onClick={() => handleViewModeChange('list')}
                  className={cn(
                    'p-2 rounded-md',
                    viewMode === 'list' && 'bg-primary-100'
                  )}
                  aria-pressed={viewMode === 'list'}
                  aria-label="List view"
                >
                  <span className="sr-only">List view</span>
                  {/* List icon */}
                </button>
              </div>
            </div>

            {/* Results Grid */}
            <ResultsGrid
              results={searchResults}
              isLoading={isLoading}
              error={error}
              viewMode={viewMode}
              onResultClick={handleResultClick}
              virtualScrollEnabled={true}
              pageSize={paginationParams.pageSize}
              ariaLive="polite"
              retryEnabled={true}
            />
          </main>
        </div>

        {/* Screen Reader Announcements */}
        <div
          ref={announcementRef}
          className="sr-only"
          role="status"
          aria-live="polite"
        />
      </div>
    </ErrorBoundary>
  );
};

export default SearchPage;