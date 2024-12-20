"use client";

import * as React from "react";
import { cn, cva, type VariantProps } from "class-variance-authority";
import LoadingSpinner from "./loading-spinner";

// Version: ^0.7.0 - class-variance-authority
// Version: ^18.2.0 - react

/**
 * Defines button style variants using class-variance-authority
 * Implements WCAG 2.1 AA compliant styles with proper contrast ratios
 * and interactive states
 */
export const buttonVariants = cva(
  // Base styles including focus handling and accessibility
  [
    "inline-flex",
    "items-center",
    "justify-center",
    "rounded-md",
    "font-medium",
    "transition-colors",
    "focus-visible:outline-none",
    "focus-visible:ring-2",
    "focus-visible:ring-offset-2",
    "disabled:pointer-events-none",
    "select-none",
    "whitespace-nowrap",
  ],
  {
    variants: {
      variant: {
        primary: [
          "bg-primary-600",
          "text-white",
          "hover:bg-primary-700",
          "focus:ring-primary-500",
          "dark:bg-primary-500",
          "dark:hover:bg-primary-600",
          "dark:focus:ring-primary-400",
        ],
        secondary: [
          "bg-neutral-200",
          "text-neutral-900",
          "hover:bg-neutral-300",
          "focus:ring-neutral-500",
          "dark:bg-neutral-700",
          "dark:text-white",
          "dark:hover:bg-neutral-600",
        ],
        outline: [
          "border-2",
          "border-primary-600",
          "text-primary-600",
          "hover:bg-primary-50",
          "focus:ring-primary-500",
          "dark:border-primary-400",
          "dark:text-primary-400",
          "dark:hover:bg-primary-950",
        ],
        ghost: [
          "text-neutral-600",
          "hover:bg-neutral-100",
          "focus:ring-neutral-500",
          "dark:text-neutral-300",
          "dark:hover:bg-neutral-800",
        ],
      },
      size: {
        sm: "text-sm px-3 py-1.5 h-8 min-w-[4rem] gap-1.5",
        md: "text-base px-4 py-2 h-10 min-w-[5rem] gap-2",
        lg: "text-lg px-6 py-3 h-12 min-w-[6rem] gap-2.5",
      },
      state: {
        disabled: "opacity-50 cursor-not-allowed focus:ring-0",
        loading: "cursor-wait focus:ring-0",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
    },
  }
);

/**
 * Props interface for Button component
 * Extends native button attributes with custom styling and state props
 */
export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  isLoading?: boolean;
  isDisabled?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  ariaLabel?: string;
  ariaDescribedBy?: string;
}

/**
 * Button Component
 * 
 * A highly reusable, accessible button component that implements the design system's
 * button patterns. Supports multiple variants, sizes, loading states, and icons.
 * Fully compliant with WCAG 2.1 AA standards.
 * 
 * @example
 * ```tsx
 * // Primary button
 * <Button>Click me</Button>
 * 
 * // Secondary button with loading state
 * <Button variant="secondary" isLoading>Processing</Button>
 * 
 * // Outline button with icon
 * <Button variant="outline" leftIcon={<Icon />}>With Icon</Button>
 * ```
 */
const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant,
      size,
      isLoading = false,
      isDisabled = false,
      leftIcon,
      rightIcon,
      children,
      className,
      ariaLabel,
      ariaDescribedBy,
      onClick,
      ...props
    },
    ref
  ) => {
    // Memoize the click handler to prevent unnecessary re-renders
    const handleClick = React.useCallback(
      (event: React.MouseEvent<HTMLButtonElement>) => {
        if (isLoading || isDisabled) {
          event.preventDefault();
          return;
        }
        onClick?.(event);
      },
      [onClick, isLoading, isDisabled]
    );

    // Determine the current state for styling
    const buttonState = React.useMemo(() => {
      if (isLoading) return "loading";
      if (isDisabled) return "disabled";
      return undefined;
    }, [isLoading, isDisabled]);

    // Compute the spinner size based on button size
    const spinnerSize = React.useMemo(() => {
      switch (size) {
        case "sm":
          return "sm";
        case "lg":
          return "lg";
        default:
          return "md";
      }
    }, [size]);

    return (
      <button
        ref={ref}
        type="button"
        disabled={isDisabled || isLoading}
        aria-disabled={isDisabled || isLoading}
        aria-label={ariaLabel}
        aria-describedby={ariaDescribedBy}
        aria-busy={isLoading}
        onClick={handleClick}
        className={cn(
          buttonVariants({ variant, size, state: buttonState }),
          className
        )}
        {...props}
      >
        {isLoading && (
          <LoadingSpinner
            size={spinnerSize}
            color={variant === "primary" ? "white" : "primary"}
            className="mr-2"
          />
        )}
        {!isLoading && leftIcon && (
          <span className="inline-flex shrink-0">{leftIcon}</span>
        )}
        <span className="inline-flex items-center">{children}</span>
        {!isLoading && rightIcon && (
          <span className="inline-flex shrink-0">{rightIcon}</span>
        )}
      </button>
    );
  }
);

// Set display name for dev tools
Button.displayName = "Button";

export default Button;