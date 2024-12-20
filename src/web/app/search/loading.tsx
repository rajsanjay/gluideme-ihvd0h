"use client";

import * as React from "react";
import LoadingSpinner from "../../../components/common/loading-spinner";

// Number of skeleton items to display in the loading state
const SKELETON_ITEMS_COUNT = 8;

/**
 * Loading component for the search page
 * Displays a skeleton UI with loading spinner during data fetching
 * Implements ARIA-compliant loading indicators and reduced motion preferences
 * 
 * @returns {JSX.Element} Loading UI skeleton with spinner and placeholder content
 */
export default function Loading(): JSX.Element {
  return (
    <div 
      role="status"
      aria-busy="true"
      aria-label="Loading search results"
      className="w-full animate-fade-in"
    >
      {/* Search Form Skeleton */}
      <div className="mb-8 space-y-4">
        <div className="flex items-center justify-between">
          <div className="h-10 w-3/4 rounded-lg bg-neutral-200 dark:bg-neutral-800 animate-pulse will-change-opacity contain-paint" />
          <div className="h-10 w-24 rounded-lg bg-neutral-200 dark:bg-neutral-800 animate-pulse will-change-opacity contain-paint" />
        </div>
        
        {/* Filter Skeleton */}
        <div className="flex gap-4">
          {[1, 2, 3].map((index) => (
            <div
              key={`filter-skeleton-${index}`}
              className="h-8 w-32 rounded-md bg-neutral-200 dark:bg-neutral-800 animate-pulse will-change-opacity contain-paint"
            />
          ))}
        </div>
      </div>

      {/* Loading Spinner */}
      <div className="flex justify-center my-8">
        <LoadingSpinner 
          size="lg"
          color="primary"
          className="mx-auto"
        />
      </div>

      {/* Results Grid Skeleton */}
      <div 
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        aria-hidden="true"
      >
        {Array.from({ length: SKELETON_ITEMS_COUNT }).map((_, index) => (
          <div
            key={`result-skeleton-${index}`}
            className="p-4 rounded-lg border border-neutral-200 dark:border-neutral-800"
          >
            {/* Result Item Content Skeleton */}
            <div className="space-y-3">
              <div className="h-6 w-3/4 rounded bg-neutral-200 dark:bg-neutral-800 animate-pulse will-change-opacity contain-paint" />
              <div className="h-4 w-1/2 rounded bg-neutral-200 dark:bg-neutral-800 animate-pulse will-change-opacity contain-paint" />
              <div className="h-4 w-2/3 rounded bg-neutral-200 dark:bg-neutral-800 animate-pulse will-change-opacity contain-paint" />
              <div className="h-4 w-1/3 rounded bg-neutral-200 dark:bg-neutral-800 animate-pulse will-change-opacity contain-paint" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}