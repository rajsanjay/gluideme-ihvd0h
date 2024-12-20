/**
 * @file SearchForm Component
 * @version 1.0.0
 * @description A comprehensive search interface component with real-time suggestions,
 * advanced filtering, and accessibility support for the Transfer Requirements Management System.
 */

import React, { useCallback, useEffect, useRef } from 'react';
import { cn } from 'class-variance-authority'; // v0.7.0
import { debounce } from 'lodash'; // v4.17.21
import { useSearch } from '../../hooks/useSearch';
import { FormField } from '../common/form-field';
import type { SearchType, SearchFilters } from '../../types/search';

// Component variants using class-variance-authority
export const searchFormVariants = {
  size: {
    default: 'w-full max-w-2xl',
    large: 'w-full max-w-4xl',
    compact: 'w-full max-w-lg'
  },
  theme: {
    light: 'bg-white border-gray-200 shadow-sm',
    dark: 'bg-gray-800 border-gray-700 shadow-dark'
  },
  state: {
    idle: 'opacity-100',
    loading: 'opacity-75',
    error: 'border-red-500'
  }
};

// Props interface for the SearchForm component
export interface SearchFormProps {
  onSearch: (query: string, type: SearchType, filters: SearchFilters) => Promise<void>;
  initialQuery?: string;
  initialType?: SearchType;
  initialFilters?: SearchFilters;
  className?: string;
  onSuggestionSelect?: (suggestion: SearchSuggestion) => void;
  analyticsEnabled?: boolean;
}

/**
 * Enhanced search form component with comprehensive functionality
 */
export const SearchForm: React.FC<SearchFormProps> = ({
  onSearch,
  initialQuery = '',
  initialType = 'requirements',
  initialFilters,
  className,
  onSuggestionSelect,
  analyticsEnabled = true
}) => {
  // Initialize search hook with configuration
  const {
    searchState,
    handleQueryChange,
    handleTypeChange,
    handleFiltersChange,
    suggestions,
    isLoading,
    error
  } = useSearch({
    initialQuery,
    initialType,
    initialFilters,
    enableHistory: true
  });

  // Refs for accessibility and analytics
  const searchInputRef = useRef<HTMLInputElement>(null);
  const announcementRef = useRef<HTMLDivElement>(null);
  const analyticsTimeoutRef = useRef<NodeJS.Timeout>();

  // Track search analytics
  const trackSearchAnalytics = useCallback(
    debounce((query: string, type: SearchType) => {
      if (analyticsEnabled && query.trim()) {
        // Implementation would integrate with your analytics system
        console.log('Search analytics:', { query, type, timestamp: new Date() });
      }
    }, 1000),
    [analyticsEnabled]
  );

  // Handle form submission
  const handleSubmit = useCallback(async (event: React.FormEvent) => {
    event.preventDefault();
    
    try {
      await onSearch(
        searchState.query,
        searchState.type,
        searchState.filters
      );

      // Announce results to screen readers
      if (announcementRef.current) {
        announcementRef.current.textContent = 'Search results updated';
      }

      // Track analytics
      trackSearchAnalytics(searchState.query, searchState.type);
    } catch (err) {
      console.error('Search error:', err);
      if (announcementRef.current) {
        announcementRef.current.textContent = 'Search failed. Please try again.';
      }
    }
  }, [onSearch, searchState, trackSearchAnalytics]);

  // Handle suggestion selection
  const handleSuggestionClick = useCallback((suggestion: SearchSuggestion) => {
    handleQueryChange(suggestion.text);
    onSuggestionSelect?.(suggestion);
    searchInputRef.current?.focus();
  }, [handleQueryChange, onSuggestionSelect]);

  // Keyboard navigation for suggestions
  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (event.key === 'ArrowDown' && suggestions.length > 0) {
      event.preventDefault();
      // Implementation for keyboard navigation
    }
  }, [suggestions]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (analyticsTimeoutRef.current) {
        clearTimeout(analyticsTimeoutRef.current);
      }
    };
  }, []);

  return (
    <form
      onSubmit={handleSubmit}
      className={cn(
        'relative',
        searchFormVariants.size.default,
        searchFormVariants.theme.light,
        isLoading && searchFormVariants.state.loading,
        error && searchFormVariants.state.error,
        className
      )}
      role="search"
      aria-label="Search transfer requirements"
    >
      <div className="flex flex-col space-y-4">
        {/* Search Input */}
        <FormField
          ref={searchInputRef}
          name="searchQuery"
          label="Search"
          type="text"
          value={searchState.query}
          onChange={handleQueryChange}
          onKeyDown={handleKeyDown}
          placeholder="Search requirements or courses..."
          error={error?.message}
          helpText="Enter keywords to search"
          required
          autoComplete={true}
          aria-controls="search-suggestions"
          aria-expanded={suggestions.length > 0}
        />

        {/* Search Type Selection */}
        <div className="flex space-x-4">
          <label className="inline-flex items-center">
            <input
              type="radio"
              name="searchType"
              value="requirements"
              checked={searchState.type === 'requirements'}
              onChange={() => handleTypeChange('requirements')}
              className="form-radio"
            />
            <span className="ml-2">Requirements</span>
          </label>
          <label className="inline-flex items-center">
            <input
              type="radio"
              name="searchType"
              value="courses"
              checked={searchState.type === 'courses'}
              onChange={() => handleTypeChange('courses')}
              className="form-radio"
            />
            <span className="ml-2">Courses</span>
          </label>
        </div>

        {/* Search Suggestions */}
        {suggestions.length > 0 && (
          <ul
            id="search-suggestions"
            className="absolute z-10 w-full mt-1 bg-white border rounded-md shadow-lg"
            role="listbox"
          >
            {suggestions.map((suggestion, index) => (
              <li
                key={`${suggestion.text}-${index}`}
                role="option"
                aria-selected={false}
                className="px-4 py-2 cursor-pointer hover:bg-gray-100"
                onClick={() => handleSuggestionClick(suggestion)}
              >
                {suggestion.text}
              </li>
            ))}
          </ul>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          className={cn(
            'px-4 py-2 text-white bg-blue-600 rounded-md',
            'hover:bg-blue-700 focus:outline-none focus:ring-2',
            'disabled:opacity-50 disabled:cursor-not-allowed'
          )}
          disabled={isLoading || !searchState.query.trim()}
        >
          {isLoading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {/* Screen Reader Announcements */}
      <div
        ref={announcementRef}
        className="sr-only"
        role="status"
        aria-live="polite"
      />
    </form>
  );
};

export default SearchForm;