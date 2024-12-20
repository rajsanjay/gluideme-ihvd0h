"use client";

import * as React from "react";
import LoadingSpinner from "../../components/common/loading-spinner";

/**
 * Dashboard Loading Component
 * 
 * Provides visual feedback during dashboard content loading with full accessibility support.
 * Implements motion-safe animations and reduced motion preferences following WCAG guidelines.
 * Follows the 8-point grid system and supports dark mode through color theming.
 * 
 * @returns {JSX.Element} An accessible loading state UI with centered spinner
 */
export default function Loading(): JSX.Element {
  return (
    <div 
      className={`
        flex min-h-[50vh] items-center justify-center
        p-8 
        bg-white dark:bg-gray-900
        motion-safe:transition-opacity motion-safe:duration-200
        motion-reduce:opacity-90
      `}
      role="status"
      aria-live="polite"
      aria-label="Loading dashboard content, please wait"
    >
      <LoadingSpinner 
        size="lg"
        color="primary"
        className="motion-safe:animate-spin motion-reduce:animate-none"
        aria-hidden="true"
      />
      <span className="sr-only">
        Loading dashboard content, please wait...
      </span>
    </div>
  );
}