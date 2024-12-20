"use client";

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

// Version: ^0.7.0 - class-variance-authority
// Version: ^18.2.0 - react

/**
 * Defines the style variants for the spinner component using class-variance-authority
 * Supports multiple sizes and colors with dark mode compatibility
 */
export const spinnerVariants = cva(
  // Base styles including animation and accessibility
  [
    "inline-block",
    "rounded-full",
    "border-2",
    "border-current",
    "border-t-transparent",
    "animate-spin",
    "motion-safe:animate-spin",
    "motion-reduce:opacity-50",
    "will-change-transform"
  ],
  {
    variants: {
      // Size variants with corresponding dimensions
      size: {
        sm: "w-4 h-4 border-2",
        md: "w-6 h-6 border-2",
        lg: "w-8 h-8 border-3",
      },
      // Color variants with dark mode support
      color: {
        primary: "text-primary-600 dark:text-primary-400",
        secondary: "text-neutral-600 dark:text-neutral-400",
        white: "text-white",
      },
    },
    // Default variants
    defaultVariants: {
      size: "md",
      color: "primary",
    },
  }
);

/**
 * Props interface for the LoadingSpinner component
 */
export interface LoadingSpinnerProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof spinnerVariants> {
  className?: string;
}

/**
 * LoadingSpinner Component
 * 
 * A highly reusable, accessible loading spinner that provides visual feedback
 * during loading states. Supports multiple sizes and colors, with built-in
 * dark mode support and reduced motion preferences.
 * 
 * @example
 * ```tsx
 * // Default usage
 * <LoadingSpinner />
 * 
 * // Custom size and color
 * <LoadingSpinner size="lg" color="white" />
 * ```
 */
const LoadingSpinner: React.FC<LoadingSpinnerProps> = React.forwardRef<
  HTMLDivElement,
  LoadingSpinnerProps
>(({ className, size, color, ...props }, ref) => {
  // Check if reduced motion is preferred
  const prefersReducedMotion = React.useMemo(
    () => window?.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches,
    []
  );

  return (
    <div
      role="status"
      aria-live="polite"
      ref={ref}
      className={spinnerVariants({ size, color, className })}
      {...props}
    >
      <span className="sr-only">
        {prefersReducedMotion ? "Loading..." : "Loading, please wait..."}
      </span>
    </div>
  );
});

// Set display name for dev tools
LoadingSpinner.displayName = "LoadingSpinner";

export default LoadingSpinner;