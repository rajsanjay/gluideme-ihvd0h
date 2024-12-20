/**
 * @file SearchBar Component
 * @version 1.0.0
 * @description A reusable search bar component providing real-time search functionality
 * with autocomplete suggestions, accessibility features, and performance optimizations.
 *
 * @requires react ^18.2.0
 * @requires class-variance-authority ^0.7.0
 * @requires lodash ^4.17.21
 */

import React, { useCallback, useEffect, useId, useRef, useState } from 'react';
import { cn } from 'class-variance-authority';
import { debounce } from 'lodash';
import { FormField } from './form-field';
import { useSearch } from '../../hooks/useSearch';
import type { SearchType } from '../../types/search';

// Search bar variants using class-variance-authority
export const searchBarVariants = cn({
  base: 'relative w-full transition-colors duration-200',
  variants: {
    size: {
      sm: 'h-8 text-sm',
      md: 'h-10 text-base',
      lg: 'h-12 text-lg'
    },
    intent: {
      primary: 'bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600',
      minimal: 'bg-transparent border-transparent'
    },
    state: {
      default: 'border-gray-300',
      focus: 'border-primary-500 ring-2 ring-primary-200',
      error: 'border-red-500 ring-2 ring-red-200',
      disabled: 'bg-gray-100 cursor-not-allowed'
    }
  },
  defaultVariants: {
    size: 'md',
    intent: 'primary',
    state: 'default'
  }
});

// Props interface with comprehensive type safety
export interface SearchBarProps {
  placeholder?: string;
  className?: string;
  type?: SearchType;
  onSearch: (query: string, type?: SearchType) => Promise<void>;
  onSuggestionSelect?: (suggestion: SearchSuggestion) => void;
  showSuggestions?: boolean;
  autoFocus?: boolean;
  disabled?: boolean;
  isLoading?: boolean;
  onError?: (error: Error) => void;
  debounceMs?: number;
}

/**
 * SearchBar component with comprehensive search functionality
 */
export const SearchBar: React.FC<SearchBarProps> = ({
  placeholder = 'Search...',
  className,
  type = 'requirements',
  onSearch,
  onSuggestionSelect,
  showSuggestions = true,
  autoFocus = false,
  disabled = false,
  isLoading = false,
  onError,
  debounceMs = 200
}) => {
  // Generate unique IDs for accessibility
  const searchId = useId();
  const suggestionListId = `${searchId}-suggestions`;
  const loadingId = `${searchId}-loading`;
  const statusId = `${searchId}-status`;

  // State management
  const [inputValue, setInputValue] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const announcerRef = useRef<HTMLDivElement>(null);

  // Initialize search hook
  const {
    handleQueryChange,
    suggestions,
    error: searchError,
    isLoading: isSearching
  } = useSearch({
    initialType: type,
    onSearchComplete: (response) => {
      if (announcerRef.current) {
        announcerRef.current.textContent = 
          `Found ${response.totalCount} results for ${inputValue}`;
      }
    }
  });

  // Debounced search handler
  const debouncedSearch = useCallback(
    debounce(async (value: string) => {
      try {
        await onSearch(value, type);
      } catch (err) {
        onError?.(err as Error);
        console.error('Search error:', err);
      }
    }, debounceMs),
    [onSearch, type, onError, debounceMs]
  );

  // Handle input changes
  const handleInputChange = useCallback((value: string) => {
    setInputValue(value);
    setSelectedIndex(-1);
    handleQueryChange(value);
    debouncedSearch(value);
  }, [handleQueryChange, debouncedSearch]);

  // Handle keyboard navigation
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (!showSuggestions || !suggestions.length) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev < suggestions.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => prev > -1 ? prev - 1 : -1);
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex > -1) {
          const selected = suggestions[selectedIndex];
          onSuggestionSelect?.(selected);
          setInputValue(selected.text);
          setSelectedIndex(-1);
        } else {
          debouncedSearch(inputValue);
        }
        break;
      case 'Escape':
        e.preventDefault();
        setSelectedIndex(-1);
        inputRef.current?.blur();
        break;
    }
  }, [showSuggestions, suggestions, selectedIndex, onSuggestionSelect, debouncedSearch, inputValue]);

  // Handle suggestion clicks
  const handleSuggestionClick = useCallback((suggestion: SearchSuggestion) => {
    onSuggestionSelect?.(suggestion);
    setInputValue(suggestion.text);
    setSelectedIndex(-1);
    inputRef.current?.focus();
  }, [onSuggestionSelect]);

  // Update aria-live region when loading state changes
  useEffect(() => {
    if (announcerRef.current) {
      announcerRef.current.textContent = isLoading || isSearching
        ? 'Searching...'
        : '';
    }
  }, [isLoading, isSearching]);

  return (
    <div className={cn('relative w-full', className)}>
      <FormField
        ref={inputRef}
        type="search"
        id={searchId}
        name="search"
        value={inputValue}
        onChange={handleInputChange}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setTimeout(() => setIsFocused(false), 200)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        autoFocus={autoFocus}
        className={searchBarVariants({
          state: disabled ? 'disabled' : isFocused ? 'focus' : 'default'
        })}
        aria-expanded={showSuggestions && suggestions.length > 0}
        aria-owns={suggestionListId}
        aria-controls={suggestionListId}
        aria-describedby={`${loadingId} ${statusId}`}
        role="combobox"
        autoComplete="off"
      />

      {/* Loading indicator */}
      {(isLoading || isSearching) && (
        <div
          id={loadingId}
          className="absolute right-3 top-1/2 -translate-y-1/2"
          aria-hidden="true"
        >
          <div className="animate-spin h-4 w-4 border-2 border-primary-500 rounded-full border-t-transparent" />
        </div>
      )}

      {/* Suggestions dropdown */}
      {showSuggestions && suggestions.length > 0 && isFocused && (
        <ul
          id={suggestionListId}
          role="listbox"
          className="absolute z-50 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md shadow-lg max-h-60 overflow-auto"
        >
          {suggestions.map((suggestion, index) => (
            <li
              key={`${suggestion.text}-${index}`}
              role="option"
              aria-selected={index === selectedIndex}
              className={cn(
                'px-4 py-2 cursor-pointer transition-colors',
                index === selectedIndex
                  ? 'bg-primary-100 dark:bg-primary-900'
                  : 'hover:bg-gray-100 dark:hover:bg-gray-700'
              )}
              onClick={() => handleSuggestionClick(suggestion)}
            >
              {suggestion.text}
            </li>
          ))}
        </ul>
      )}

      {/* Error message */}
      {(searchError || error) && (
        <div
          id={statusId}
          className="text-red-500 dark:text-red-400 text-sm mt-1"
          role="alert"
        >
          {searchError?.message || error?.message}
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

export default SearchBar;