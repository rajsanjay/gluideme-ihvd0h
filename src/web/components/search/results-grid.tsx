"use client";

import * as React from "react";
import { cn } from "class-variance-authority"; // v0.7.0
import { useVirtualizer } from "@tanstack/react-virtual"; // v3.0.0
import { useIntersectionObserver } from "@hooks/useIntersectionObserver"; // v1.0.0

import Card from "../common/card";
import VirtualizedDataTable from "../common/data-table";
import ErrorBoundary from "../common/error-boundary";
import { useSearch } from "../../hooks/useSearch";
import { formatInstitutionName, truncateText } from "../../lib/utils/format";
import type { SearchResult } from "../../types/search";

// Grid layout variants using class-variance-authority
const gridVariants = {
  base: "grid gap-4 relative min-h-[200px]",
  grid: {
    sm: "grid-cols-1 gap-y-4",
    md: "grid-cols-2 gap-4",
    lg: "grid-cols-3 gap-6",
    xl: "grid-cols-4 gap-6",
    "2xl": "grid-cols-5 gap-8",
  },
  list: {
    sm: "grid-cols-1 gap-2",
    md: "grid-cols-1 gap-2",
    lg: "grid-cols-1 gap-2",
  },
};

// Props interface with comprehensive type definitions
export interface ResultsGridProps {
  results: SearchResult[];
  isLoading: boolean;
  error: Error | null;
  viewMode: "grid" | "list";
  onResultClick: (result: SearchResult) => void;
  className?: string;
  virtualScrollEnabled?: boolean;
  pageSize?: number;
  ariaLive?: "polite" | "assertive";
  retryEnabled?: boolean;
}

/**
 * Renders an individual search result item with accessibility features
 */
const ResultItem = React.memo(
  ({ 
    result, 
    onClick, 
    isVirtualized 
  }: { 
    result: SearchResult; 
    onClick: (result: SearchResult) => void; 
    isVirtualized?: boolean;
  }) => {
    const ref = React.useRef<HTMLDivElement>(null);
    const { isIntersecting } = useIntersectionObserver(ref, {
      threshold: 0.1,
      skip: !isVirtualized,
    });

    const handleKeyDown = React.useCallback(
      (e: React.KeyboardEvent) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onClick(result);
        }
      },
      [onClick, result]
    );

    return (
      <div ref={ref}>
        <Card
          variant="outline"
          padding="lg"
          interactive
          className={cn(
            "transition-opacity duration-200",
            isVirtualized && !isIntersecting && "opacity-0"
          )}
          onClick={() => onClick(result)}
          onKeyDown={handleKeyDown}
          role="article"
          tabIndex={0}
          aria-label={`${result.title} from ${result.institution}`}
        >
          <div className="space-y-2">
            <h3 className="text-lg font-semibold line-clamp-2">{result.title}</h3>
            <p className="text-sm text-neutral-600 dark:text-neutral-300">
              {formatInstitutionName(result.institution)}
            </p>
            <p className="text-sm line-clamp-3">
              {truncateText(result.description, 150)}
            </p>
            <div className="flex items-center gap-2 text-xs text-neutral-500">
              <span>{result.majorCategory}</span>
              <span>•</span>
              <span>{new Date(result.effectiveDate).toLocaleDateString()}</span>
              <span>•</span>
              <span className="capitalize">{result.status}</span>
            </div>
          </div>
        </Card>
      </div>
    );
  }
);

ResultItem.displayName = "ResultItem";

/**
 * ResultsGrid component for displaying search results with virtualization
 * and accessibility support
 */
export const ResultsGrid: React.FC<ResultsGridProps> = ({
  results,
  isLoading,
  error,
  viewMode,
  onResultClick,
  className,
  virtualScrollEnabled = true,
  pageSize = 20,
  ariaLive = "polite",
  retryEnabled = true,
}) => {
  // Container ref for virtualization
  const containerRef = React.useRef<HTMLDivElement>(null);

  // Initialize virtualizer if enabled
  const rowVirtualizer = virtualScrollEnabled
    ? useVirtualizer({
        count: results.length,
        getScrollElement: () => containerRef.current,
        estimateSize: () => (viewMode === "grid" ? 280 : 180),
        overscan: 5,
      })
    : null;

  // Memoized grid classes
  const gridClasses = React.useMemo(
    () =>
      cn(
        gridVariants.base,
        viewMode === "grid" ? gridVariants.grid : gridVariants.list,
        className
      ),
    [viewMode, className]
  );

  // Loading state renderer
  const renderLoading = () => (
    <div
      className="flex items-center justify-center h-64"
      role="status"
      aria-label="Loading results"
    >
      <div className="animate-pulse space-y-4 w-full">
        {Array.from({ length: 3 }).map((_, idx) => (
          <div
            key={idx}
            className="bg-neutral-200 dark:bg-neutral-700 h-32 rounded-lg"
          />
        ))}
      </div>
    </div>
  );

  // Error state renderer
  const renderError = () => (
    <div
      className="flex flex-col items-center justify-center h-64 text-center"
      role="alert"
    >
      <p className="text-red-600 mb-4">{error?.message}</p>
      {retryEnabled && (
        <button
          onClick={() => window.location.reload()}
          className="text-primary-600 hover:underline focus:outline-none focus:ring-2 focus:ring-primary-500 rounded"
        >
          Retry
        </button>
      )}
    </div>
  );

  // Empty state renderer
  const renderEmpty = () => (
    <div
      className="flex items-center justify-center h-64 text-neutral-500"
      role="status"
    >
      No results found
    </div>
  );

  // Main content renderer
  const renderContent = () => {
    if (isLoading) return renderLoading();
    if (error) return renderError();
    if (!results.length) return renderEmpty();

    return viewMode === "list" ? (
      <VirtualizedDataTable
        data={results}
        columns={[
          {
            header: "Title",
            accessorKey: "title",
          },
          {
            header: "Institution",
            accessorKey: "institution",
            cell: ({ row }) => formatInstitutionName(row.original.institution),
          },
          {
            header: "Category",
            accessorKey: "majorCategory",
          },
          {
            header: "Status",
            accessorKey: "status",
            cell: ({ row }) => (
              <span className="capitalize">{row.original.status}</span>
            ),
          },
        ]}
        onRowClick={(row) => onResultClick(row.original)}
        virtualScrolling={virtualScrollEnabled}
      />
    ) : (
      <div
        ref={containerRef}
        className={gridClasses}
        style={{
          height: virtualScrollEnabled ? "800px" : "auto",
          overflow: virtualScrollEnabled ? "auto" : "visible",
        }}
      >
        {rowVirtualizer
          ? rowVirtualizer.getVirtualItems().map((virtualRow) => (
              <ResultItem
                key={results[virtualRow.index].id}
                result={results[virtualRow.index]}
                onClick={onResultClick}
                isVirtualized
              />
            ))
          : results.map((result) => (
              <ResultItem
                key={result.id}
                result={result}
                onClick={onResultClick}
              />
            ))}
      </div>
    );
  };

  return (
    <ErrorBoundary
      fallback={
        <div className="text-red-600 p-4" role="alert">
          An error occurred while displaying results
        </div>
      }
    >
      <div
        aria-live={ariaLive}
        aria-busy={isLoading}
        aria-label="Search results"
        className="relative"
      >
        {renderContent()}
      </div>
    </ErrorBoundary>
  );
};

ResultsGrid.displayName = "ResultsGrid";

export default ResultsGrid;