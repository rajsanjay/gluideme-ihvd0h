"use client";

import * as React from "react";
import LoadingSpinner from "@/components/common/loading-spinner";

// Version: ^18.2.0 - react

/**
 * Constants for styling and accessibility
 */
const CONTAINER_STYLES = [
  "fixed",
  "inset-0",
  "z-50",
  "flex",
  "items-center",
  "justify-center",
  "min-h-screen",
  "bg-background/80",
  "backdrop-blur-sm",
  "transition-opacity",
  "duration-200",
  "contain-strict",
  "safe-area-inset-x-4",
  "safe-area-inset-y-4"
].join(" ");

const SPINNER_CONFIG = {
  size: "lg" as const,
  color: "primary" as const,
  className: "animate-spin-smooth"
};

const ARIA_LABELS = {
  role: "status" as const,
  "aria-live": "polite" as const,
  "aria-label": "Loading content"
};

/**
 * Loading Component
 * 
 * Displays during page transitions and data fetching operations in the student section.
 * Features:
 * - Responsive design with safe area insets
 * - Enhanced accessibility with ARIA labels
 * - Smooth animations with reduced motion support
 * - Backdrop blur for depth perception
 * - Performance optimized with CSS containment
 * 
 * @returns {JSX.Element} Loading spinner with optimized layout and animations
 */
const Loading: React.FC = () => {
  // Check for reduced motion preference
  const prefersReducedMotion = React.useMemo(
    () => window?.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches,
    []
  );

  return (
    <div 
      className={CONTAINER_STYLES}
      style={{
        // Enable hardware acceleration and optimize animations
        willChange: "opacity",
        // Ensure smooth opacity transitions
        opacity: 1,
        // Support for older browsers
        WebkitBackdropFilter: "blur(8px)",
      }}
      {...ARIA_LABELS}
    >
      <div 
        className={
          prefersReducedMotion 
            ? "motion-reduce:transform-none" 
            : "animate-fade-in"
        }
      >
        <LoadingSpinner
          {...SPINNER_CONFIG}
          // Additional accessibility for screen readers
          aria-label={
            prefersReducedMotion 
              ? "Loading content" 
              : "Loading content, please wait"
          }
        />
      </div>
    </div>
  );
};

export default Loading;