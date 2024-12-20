import { useState, useCallback, useRef, useEffect } from 'react'; // v18.2.0
import type { PaginationParams } from '../types/common';

/**
 * Props for configuring the usePagination hook
 */
interface UsePaginationProps {
  /** Initial page number (1-based) */
  initialPage: number;
  /** Initial number of items per page */
  initialPageSize: number;
  /** Total number of items across all pages */
  totalItems: number;
  /** Callback fired when pagination parameters change */
  onPageChange: (params: PaginationParams) => void;
  /** Optional debounce delay in milliseconds */
  debounceMs?: number;
}

/**
 * Calculates the total number of pages with sophisticated edge case handling
 * @param totalItems - Total number of items
 * @param pageSize - Number of items per page
 * @returns Total number of pages (minimum 1)
 */
const calculateTotalPages = (totalItems: number, pageSize: number): number => {
  // Handle invalid inputs
  if (totalItems < 0 || pageSize <= 0) {
    console.warn('Invalid pagination parameters detected');
    return 1;
  }

  // Handle edge case of no items
  if (totalItems === 0) {
    return 1;
  }

  return Math.max(Math.ceil(totalItems / pageSize), 1);
};

/**
 * Advanced hook for managing pagination state with performance optimizations
 * and accessibility features
 * 
 * @example
 * ```tsx
 * const {
 *   paginationParams,
 *   totalPages,
 *   handlePageChange,
 *   handlePageSizeChange,
 *   canPreviousPage,
 *   canNextPage,
 *   isLoading,
 *   error
 * } = usePagination({
 *   initialPage: 1,
 *   initialPageSize: 10,
 *   totalItems: 100,
 *   onPageChange: (params) => fetchData(params),
 *   debounceMs: 300
 * });
 * ```
 */
export const usePagination = ({
  initialPage,
  initialPageSize,
  totalItems,
  onPageChange,
  debounceMs = 300
}: UsePaginationProps) => {
  // Validate initial values
  const validatedInitialPage = Math.max(1, Math.floor(initialPage));
  const validatedInitialPageSize = Math.max(1, Math.floor(initialPageSize));

  // State management
  const [paginationParams, setPaginationParams] = useState<PaginationParams>({
    page: validatedInitialPage,
    pageSize: validatedInitialPageSize
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  // Refs for debouncing
  const timeoutRef = useRef<NodeJS.Timeout>();
  const isMountedRef = useRef(true);

  // Calculate derived values
  const totalPages = calculateTotalPages(totalItems, paginationParams.pageSize);
  const canPreviousPage = paginationParams.page > 1;
  const canNextPage = paginationParams.page < totalPages;

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  /**
   * Memoized handler for page changes with debouncing and validation
   */
  const handlePageChange = useCallback((newPage: number) => {
    try {
      // Validate page number
      const validatedPage = Math.max(1, Math.min(Math.floor(newPage), totalPages));

      // Update state immediately for UI responsiveness
      setPaginationParams(prev => ({
        ...prev,
        page: validatedPage
      }));

      // Clear any existing timeout
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      // Set loading state
      setIsLoading(true);
      setError(null);

      // Debounce the actual data fetch
      timeoutRef.current = setTimeout(() => {
        if (isMountedRef.current) {
          onPageChange({
            page: validatedPage,
            pageSize: paginationParams.pageSize
          }).catch((err: Error) => {
            if (isMountedRef.current) {
              setError(err);
              console.error('Pagination error:', err);
            }
          }).finally(() => {
            if (isMountedRef.current) {
              setIsLoading(false);
            }
          });
        }
      }, debounceMs);
    } catch (err) {
      setError(err as Error);
      console.error('Page change error:', err);
    }
  }, [totalPages, paginationParams.pageSize, onPageChange, debounceMs]);

  /**
   * Memoized handler for page size changes with validation
   */
  const handlePageSizeChange = useCallback((newPageSize: number) => {
    try {
      // Validate page size
      const validatedPageSize = Math.max(1, Math.floor(newPageSize));
      
      // Calculate new page number to maintain approximate position
      const currentFirstItem = (paginationParams.page - 1) * paginationParams.pageSize;
      const newPage = Math.max(1, Math.ceil(currentFirstItem / validatedPageSize) + 1);

      // Update state
      setPaginationParams({
        page: newPage,
        pageSize: validatedPageSize
      });

      // Notify parent component
      setIsLoading(true);
      setError(null);

      onPageChange({
        page: newPage,
        pageSize: validatedPageSize
      }).catch((err: Error) => {
        if (isMountedRef.current) {
          setError(err);
          console.error('Page size change error:', err);
        }
      }).finally(() => {
        if (isMountedRef.current) {
          setIsLoading(false);
        }
      });
    } catch (err) {
      setError(err as Error);
      console.error('Page size change error:', err);
    }
  }, [paginationParams, onPageChange]);

  return {
    paginationParams,
    totalPages,
    handlePageChange,
    handlePageSizeChange,
    canPreviousPage,
    canNextPage,
    isLoading,
    error
  };
};

export default usePagination;