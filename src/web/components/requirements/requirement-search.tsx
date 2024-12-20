/**
 * @file RequirementSearch Component
 * @version 1.0.0
 * @description A specialized search component for transfer requirements with enhanced features
 * including progressive loading, analytics, and accessibility support.
 *
 * @requires react ^18.2.0
 * @requires use-debounce ^9.0.0
 * @requires class-variance-authority ^0.7.0
 */

import React, { useCallback, useEffect, useRef } from 'react';
import { cn } from 'class-variance-authority';
import { useDebounce } from 'use-debounce';

import { SearchBar, type SearchBarProps } from '../common/search-bar';
import { useSearch } from '../../hooks/useSearch';
import type { SearchType } from '../../types/search';
import { usePagination } from '../../hooks/usePagination';

// Default configuration values
const DEFAULT_DEBOUNCE_MS = 200;
const DEFAULT_PAGE_SIZE = 20;

export interface RequirementSearchProps {
  /** Optional class name for styling */
  className?: string;
  /** Callback fired when search is completed */
  onSearchComplete?: (response: SearchResponse) => void;
  /** Whether to show filter options */
  showFilters?: boolean;
  /** Whether to auto-focus the search input */
  autoFocus?: boolean;
  /** Debounce delay in milliseconds */
  debounceMs?: number;
  /** Analytics configuration */
  analyticsConfig?: {
    trackSearches?: boolean;
    trackFilters?: boolean;
    trackSuggestions?: boolean;
  };
  /** Accessibility configuration */
  accessibilityConfig?: {
    announceResults?: boolean;
    ariaLabel?: string;
    ariaDescribedBy?: string;
  };
  /** Cache configuration */
  cacheConfig?: {
    enabled?: boolean;
    timeout?: number;
  };
}

/**
 * RequirementSearch component providing comprehensive search functionality
 * for transfer requirements with enhanced features and accessibility
 */
export const RequirementSearch: React.FC<RequirementSearchProps> = ({
  className,
  onSearchComplete,
  showFilters = true,
  autoFocus = false,
  debounceMs = DEFAULT_DEBOUNCE_MS,
  analyticsConfig = {
    trackSearches: true,
    trackFilters: true,
    trackSuggestions: true
  },
  accessibilityConfig = {
    announceResults: true,
    ariaLabel: 'Search transfer requirements',
    ariaDescribedBy: 'search-description'
  },
  cacheConfig = {
    enabled: true,
    timeout: 5 * 60 * 1000 // 5 minutes
  }
}) => {
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
    suggestions,
    searchHistory,
    cancelSearch,
    resetSearch,
    paginationParams
  } = useSearch({
    initialType: 'requirements',
    onSearchComplete,
    enableHistory: analyticsConfig.trackSearches,
    cacheTimeout: cacheConfig.enabled ? cacheConfig.timeout : 0
  });

  // Initialize pagination
  const { handlePageChange } = usePagination({
    initialPage: 1,
    initialPageSize: DEFAULT_PAGE_SIZE,
    totalItems: totalResults,
    onPageChange: async (params) => {
      await handleQueryChange(searchState.query);
    }
  });

  // Refs for accessibility and cleanup
  const announcerRef = useRef<HTMLDivElement>(null);
  const searchBarRef = useRef<HTMLDivElement>(null);

  // Debounced search handler
  const [debouncedSearch] = useDebounce(
    (query: string) => handleQueryChange(query),
    debounceMs
  );

  /**
   * Handle suggestion selection with analytics
   */
  const handleSuggestionSelect = useCallback((suggestion: SearchSuggestion) => {
    if (analyticsConfig.trackSuggestions) {
      // Track suggestion selection
      console.log('Suggestion selected:', suggestion);
    }

    handleQueryChange(suggestion.text);
    if (suggestion.type !== searchState.type) {
      handleTypeChange(suggestion.type);
    }

    // Announce selection to screen readers
    if (accessibilityConfig.announceResults && announcerRef.current) {
      announcerRef.current.textContent = `Selected suggestion: ${suggestion.text}`;
    }
  }, [
    analyticsConfig.trackSuggestions,
    handleQueryChange,
    handleTypeChange,
    searchState.type,
    accessibilityConfig.announceResults
  ]);

  /**
   * Handle filter changes with analytics
   */
  const handleFilterChange = useCallback((filters: SearchFilters) => {
    if (analyticsConfig.trackFilters) {
      // Track filter changes
      console.log('Filters changed:', filters);
    }

    handleFiltersChange(filters);
  }, [analyticsConfig.trackFilters, handleFiltersChange]);

  /**
   * Update accessibility announcements when results change
   */
  useEffect(() => {
    if (accessibilityConfig.announceResults && announcerRef.current) {
      const message = isLoading
        ? 'Searching...'
        : error
        ? `Search error: ${error.message}`
        : `Found ${totalResults} results for "${searchState.query}"`;
      
      announcerRef.current.textContent = message;
    }
  }, [
    isLoading,
    error,
    totalResults,
    searchState.query,
    accessibilityConfig.announceResults
  ]);

  return (
    <div className={cn('relative w-full', className)}>
      {/* Search description for screen readers */}
      <div id="search-description" className="sr-only">
        Search for transfer requirements across institutions. Use filters to refine results.
      </div>

      {/* Main search bar */}
      <SearchBar
        ref={searchBarRef}
        placeholder="Search transfer requirements..."
        value={searchState.query}
        onSearch={debouncedSearch}
        onSuggestionSelect={handleSuggestionSelect}
        showSuggestions={true}
        autoFocus={autoFocus}
        disabled={isLoading}
        isLoading={isLoading}
        onError={(error) => console.error('Search error:', error)}
        debounceMs={debounceMs}
        aria-label={accessibilityConfig.ariaLabel}
        aria-describedby={accessibilityConfig.ariaDescribedBy}
      />

      {/* Filter section */}
      {showFilters && (
        <div className="mt-4 space-y-4">
          {/* Filter implementation based on SearchFilters type */}
          {/* Institution type filter */}
          {/* Major category filter */}
          {/* Date range filter */}
          {/* Status filter */}
        </div>
      )}

      {/* Search results */}
      {searchResults.length > 0 && (
        <div
          className="mt-6 space-y-4"
          role="region"
          aria-label="Search results"
          aria-live="polite"
        >
          {searchResults.map((result) => (
            <div
              key={result.id}
              className="p-4 bg-white rounded-lg shadow-sm"
              role="article"
            >
              <h3 className="text-lg font-semibold">{result.title}</h3>
              <p className="mt-1 text-gray-600">{result.description}</p>
              <div className="mt-2 text-sm text-gray-500">
                {result.institution} • {result.majorCategory}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* No results message */}
      {!isLoading && searchState.query && searchResults.length === 0 && (
        <div
          className="mt-6 text-center text-gray-500"
          role="status"
        >
          No results found for "{searchState.query}"
        </div>
      )}

      {/* Error message */}
      {error && (
        <div
          className="mt-4 p-4 bg-red-50 text-red-700 rounded-md"
          role="alert"
        >
          {error.message}
        </div>
      )}

      {/* Live region for screen reader announcements */}
      <div
        ref={announcerRef}
        className="sr-only"
        role="status"
        aria-live="polite"
      />
    </div>
  );
};

export default RequirementSearch;