"use client";

import * as React from "react";
import { cn } from "class-variance-authority";
import { Button, buttonVariants } from "./button";

// Version: ^18.2.0 - react
// Version: ^0.7.0 - class-variance-authority

/**
 * Pagination component variants using class-variance-authority
 * Implements responsive and accessible styles
 */
const paginationVariants = {
  base: "flex items-center justify-between gap-2 px-4 py-3 sm:px-6",
  pageButton: "relative inline-flex items-center px-4 py-2 text-sm font-medium rounded-md min-w-[44px] min-h-[44px]",
  activeButton: "bg-primary-600 text-white hover:bg-primary-700 focus:ring-2 focus:ring-primary-500",
  inactiveButton: "bg-white text-neutral-700 hover:bg-neutral-50 focus:ring-2 focus:ring-neutral-500",
  disabledButton: "opacity-50 cursor-not-allowed pointer-events-none",
  mobileLayout: "flex-col items-center gap-4 sm:flex-row",
  pageSizeSelect: "ml-2 rounded-md border-neutral-300 py-2 pl-3 pr-10 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
};

/**
 * Props interface for the Pagination component
 */
interface PaginationProps {
  currentPage: number;
  pageSize: number;
  totalItems: number;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
  pageSizeOptions?: number[];
  className?: string;
  showPageSizeSelector?: boolean;
  ariaLabels?: {
    nextPage: string;
    prevPage: string;
    pageNumber: string;
  };
  responsive?: boolean;
}

/**
 * Generates an array of page numbers with smart ellipsis placement
 */
const getPageNumbers = (currentPage: number, totalPages: number, maxVisible: number = 5): number[] => {
  const pages: number[] = [];
  
  if (totalPages <= maxVisible) {
    return Array.from({ length: totalPages }, (_, i) => i + 1);
  }

  // Always show first and last page
  pages.push(1);
  
  let startPage = Math.max(2, currentPage - Math.floor(maxVisible / 2));
  let endPage = Math.min(totalPages - 1, startPage + maxVisible - 3);
  
  if (startPage > 2) pages.push(-1); // Left ellipsis
  
  for (let i = startPage; i <= endPage; i++) {
    pages.push(i);
  }
  
  if (endPage < totalPages - 1) pages.push(-1); // Right ellipsis
  if (totalPages > 1) pages.push(totalPages);
  
  return pages;
};

/**
 * Pagination Component
 * 
 * A comprehensive pagination component that provides accessible navigation controls
 * for paginated data displays. Features responsive design, keyboard navigation,
 * and customizable page size selection.
 * 
 * @example
 * ```tsx
 * <Pagination
 *   currentPage={1}
 *   pageSize={10}
 *   totalItems={100}
 *   onPageChange={(page) => handlePageChange(page)}
 *   showPageSizeSelector
 * />
 * ```
 */
const Pagination: React.FC<PaginationProps> = React.memo(({
  currentPage,
  pageSize,
  totalItems,
  onPageChange,
  onPageSizeChange,
  pageSizeOptions = [10, 25, 50, 100],
  className,
  showPageSizeSelector = false,
  ariaLabels = {
    nextPage: "Next page",
    prevPage: "Previous page",
    pageNumber: "Page"
  },
  responsive = true
}) => {
  // Calculate total pages
  const totalPages = React.useMemo(() => 
    Math.max(1, Math.ceil(totalItems / pageSize)),
    [totalItems, pageSize]
  );

  // Generate page numbers with memoization
  const pageNumbers = React.useMemo(() => 
    getPageNumbers(currentPage, totalPages),
    [currentPage, totalPages]
  );

  // Navigation state
  const isFirstPage = currentPage === 1;
  const isLastPage = currentPage === totalPages;

  // Keyboard navigation handler
  const handleKeyDown = React.useCallback((e: React.KeyboardEvent, page: number) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onPageChange(page);
    }
  }, [onPageChange]);

  // Debounced page size change handler
  const handlePageSizeChange = React.useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    const newSize = parseInt(e.target.value, 10);
    onPageSizeChange?.(newSize);
  }, [onPageSizeChange]);

  return (
    <nav
      role="navigation"
      aria-label="Pagination"
      className={cn(
        paginationVariants.base,
        responsive && paginationVariants.mobileLayout,
        className
      )}
    >
      {/* Page size selector */}
      {showPageSizeSelector && onPageSizeChange && (
        <div className="flex items-center text-sm">
          <label htmlFor="pageSize" className="mr-2">
            Items per page:
          </label>
          <select
            id="pageSize"
            value={pageSize}
            onChange={handlePageSizeChange}
            className={paginationVariants.pageSizeSelect}
            aria-label="Select number of items per page"
          >
            {pageSizeOptions.map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Pagination controls */}
      <div className="flex items-center gap-1">
        {/* Previous page button */}
        <Button
          onClick={() => !isFirstPage && onPageChange(currentPage - 1)}
          disabled={isFirstPage}
          aria-label={ariaLabels.prevPage}
          aria-disabled={isFirstPage}
          variant="outline"
          size="sm"
        >
          Previous
        </Button>

        {/* Page numbers */}
        <div className="hidden sm:flex items-center gap-1">
          {pageNumbers.map((pageNum, idx) => {
            if (pageNum === -1) {
              return (
                <span
                  key={`ellipsis-${idx}`}
                  className="px-4 py-2"
                  aria-hidden="true"
                >
                  ...
                </span>
              );
            }

            const isActive = pageNum === currentPage;
            return (
              <button
                key={pageNum}
                onClick={() => onPageChange(pageNum)}
                onKeyDown={(e) => handleKeyDown(e, pageNum)}
                className={cn(
                  paginationVariants.pageButton,
                  isActive
                    ? paginationVariants.activeButton
                    : paginationVariants.inactiveButton
                )}
                aria-label={`${ariaLabels.pageNumber} ${pageNum}`}
                aria-current={isActive ? "page" : undefined}
              >
                {pageNum}
              </button>
            );
          })}
        </div>

        {/* Current page indicator for mobile */}
        <span className="sm:hidden text-sm">
          Page {currentPage} of {totalPages}
        </span>

        {/* Next page button */}
        <Button
          onClick={() => !isLastPage && onPageChange(currentPage + 1)}
          disabled={isLastPage}
          aria-label={ariaLabels.nextPage}
          aria-disabled={isLastPage}
          variant="outline"
          size="sm"
        >
          Next
        </Button>
      </div>
    </nav>
  );
});

// Set display name for dev tools
Pagination.displayName = "Pagination";

export default Pagination;