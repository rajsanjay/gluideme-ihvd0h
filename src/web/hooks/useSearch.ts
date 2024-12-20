import { useState, useCallback, useEffect, useRef } from 'react'; // v18.2.0
import { debounce } from 'lodash'; // v4.17.21
import { useSearchHistory } from '@tanstack/react-query'; // v4.0.0

import type { 
  SearchParams, 
  SearchResponse, 
  SearchResult, 
  SearchType,
  SearchFilters,
  SearchSuggestion
} from '../../types/search';
import { usePagination } from '../hooks/usePagination';

// Constants for configuration
const DEBOUNCE_MS = 200;
const DEFAULT_CACHE_TIMEOUT = 5 * 60 * 1000; // 5 minutes
const MIN_QUERY_LENGTH = 2;

interface SearchError extends Error {
  code: string;
  details?: unknown;
}

interface SearchState {
  query: string;
  type: SearchType;
  filters: SearchFilters;
  lastSearched: Date | null;
  searchId: string;
}

interface UseSearchProps {
  initialQuery?: string;
  initialType?: SearchType;
  initialFilters?: SearchFilters;
  onSearchComplete?: (response: SearchResponse) => void;
  enableHistory?: boolean;
  cacheTimeout?: number;
}

/**
 * Custom hook for managing search operations with optimized performance
 * and accessibility support
 */
export const useSearch = ({
  initialQuery = '',
  initialType = 'requirements',
  initialFilters = {
    institutionTypes: [],
    majorCategories: [],
    effectiveDate: { startDate: '', endDate: '' },
    status: 'active'
  },
  onSearchComplete,
  enableHistory = true,
  cacheTimeout = DEFAULT_CACHE_TIMEOUT
}: UseSearchProps = {}) => {
  // State management
  const [searchState, setSearchState] = useState<SearchState>({
    query: initialQuery,
    type: initialType,
    filters: initialFilters,
    lastSearched: null,
    searchId: crypto.randomUUID()
  });

  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [totalResults, setTotalResults] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<SearchError | null>(null);
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([]);

  // Refs for cleanup and caching
  const abortControllerRef = useRef<AbortController>();
  const cacheRef = useRef<Map<string, { data: SearchResponse; timestamp: number }>>(
    new Map()
  );
  const announcementRef = useRef<HTMLDivElement>(null);

  // Initialize pagination
  const { paginationParams, handlePageChange } = usePagination({
    initialPage: 1,
    initialPageSize: 20,
    totalItems: totalResults,
    onPageChange: async (params) => {
      await performSearch(searchState.query, params);
    }
  });

  // Initialize search history if enabled
  const { data: searchHistory = [], mutate: updateHistory } = useSearchHistory({
    enabled: enableHistory
  });

  /**
   * Cleanup function for aborting requests and clearing cache
   */
  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
      clearCache();
    };
  }, []);

  /**
   * Clear expired cache entries
   */
  const clearCache = useCallback(() => {
    const now = Date.now();
    cacheRef.current.forEach((entry, key) => {
      if (now - entry.timestamp > cacheTimeout) {
        cacheRef.current.delete(key);
      }
    });
  }, [cacheTimeout]);

  /**
   * Generate cache key for search parameters
   */
  const getCacheKey = useCallback((query: string, params: SearchParams): string => {
    return JSON.stringify({
      query,
      type: searchState.type,
      filters: searchState.filters,
      pagination: params
    });
  }, [searchState.type, searchState.filters]);

  /**
   * Debounced search function with caching and error handling
   */
  const performSearch = useCallback(
    debounce(async (query: string, paginationParams: typeof usePagination.paginationParams) => {
      try {
        // Abort previous request if exists
        abortControllerRef.current?.abort();
        abortControllerRef.current = new AbortController();

        // Check cache first
        const cacheKey = getCacheKey(query, { ...searchState, pagination: paginationParams });
        const cachedResult = cacheRef.current.get(cacheKey);
        
        if (cachedResult && Date.now() - cachedResult.timestamp < cacheTimeout) {
          setSearchResults(cachedResult.data.results);
          setTotalResults(cachedResult.data.totalCount);
          onSearchComplete?.(cachedResult.data);
          return;
        }

        setIsLoading(true);
        setError(null);

        // Prepare search request
        const response = await fetch('/api/search', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query,
            type: searchState.type,
            filters: searchState.filters,
            pagination: paginationParams
          }),
          signal: abortControllerRef.current.signal
        });

        if (!response.ok) {
          throw new Error(`Search failed: ${response.statusText}`);
        }

        const searchResponse: SearchResponse = await response.json();

        // Update cache
        cacheRef.current.set(cacheKey, {
          data: searchResponse,
          timestamp: Date.now()
        });

        // Update state
        setSearchResults(searchResponse.results);
        setTotalResults(searchResponse.totalCount);
        
        // Update search history
        if (enableHistory && query.trim()) {
          updateHistory({
            type: 'add',
            entry: {
              query,
              timestamp: new Date().toISOString(),
              type: searchState.type
            }
          });
        }

        // Announce results to screen readers
        if (announcementRef.current) {
          announcementRef.current.textContent = 
            `Found ${searchResponse.totalCount} results for ${query}`;
        }

        onSearchComplete?.(searchResponse);
      } catch (err) {
        if (err.name !== 'AbortError') {
          const searchError: SearchError = new Error('Search failed');
          searchError.code = 'SEARCH_ERROR';
          searchError.details = err;
          setError(searchError);
          console.error('Search error:', err);
        }
      } finally {
        setIsLoading(false);
      }
    }, DEBOUNCE_MS),
    [searchState, cacheTimeout, enableHistory, onSearchComplete, getCacheKey]
  );

  /**
   * Handle query changes with validation
   */
  const handleQueryChange = useCallback((query: string) => {
    setSearchState(prev => ({
      ...prev,
      query,
      lastSearched: null
    }));

    if (query.length >= MIN_QUERY_LENGTH) {
      performSearch(query, paginationParams);
    } else {
      setSearchResults([]);
      setTotalResults(0);
    }
  }, [paginationParams, performSearch]);

  /**
   * Handle search type changes
   */
  const handleTypeChange = useCallback((type: SearchType) => {
    setSearchState(prev => ({
      ...prev,
      type,
      lastSearched: null
    }));
    if (searchState.query.length >= MIN_QUERY_LENGTH) {
      performSearch(searchState.query, paginationParams);
    }
  }, [searchState.query, paginationParams, performSearch]);

  /**
   * Handle filter changes
   */
  const handleFiltersChange = useCallback((filters: SearchFilters) => {
    setSearchState(prev => ({
      ...prev,
      filters,
      lastSearched: null
    }));
    if (searchState.query.length >= MIN_QUERY_LENGTH) {
      performSearch(searchState.query, paginationParams);
    }
  }, [searchState.query, paginationParams, performSearch]);

  /**
   * Cancel ongoing search request
   */
  const cancelSearch = useCallback(() => {
    abortControllerRef.current?.abort();
    setIsLoading(false);
  }, []);

  /**
   * Reset search state
   */
  const resetSearch = useCallback(() => {
    setSearchState({
      query: '',
      type: initialType,
      filters: initialFilters,
      lastSearched: null,
      searchId: crypto.randomUUID()
    });
    setSearchResults([]);
    setTotalResults(0);
    setSuggestions([]);
    setError(null);
  }, [initialType, initialFilters]);

  return {
    searchState,
    searchResults,
    totalResults,
    isLoading,
    error,
    handleQueryChange,
    handleTypeChange,
    handleFiltersChange,
    handlePageChange,
    suggestions,
    searchHistory,
    cancelSearch,
    resetSearch,
    paginationParams
  };
};

export default useSearch;