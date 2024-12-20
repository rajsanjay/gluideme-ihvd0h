/**
 * @file Card Component
 * @version 1.0.0
 * @description A reusable card component implementing the design system's visual hierarchy
 * with theme integration, RTL support, and WCAG 2.1 AA compliance.
 */

import React from 'react';
import { cn } from '@shadcn/ui'; // v0.1.0
import { colors, spacing, transitions } from '../../config/theme';

// Type definitions
export type CardVariant = 'default' | 'outline' | 'ghost' | 'elevated';
export type PaddingSize = 'none' | 'sm' | 'md' | 'lg' | 'responsive';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Visual style variant of the card */
  variant?: CardVariant;
  /** Padding size following 8-point grid system */
  padding?: PaddingSize;
  /** Enable hover and focus states */
  interactive?: boolean;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Generates theme-aware class names for card styling
 * @param props Card properties and theme tokens
 * @returns Combined class names string
 */
const getCardClasses = ({
  variant = 'default',
  padding = 'md',
  interactive = false,
  className,
}: CardProps): string => {
  // Base classes with RTL support
  const baseClasses = cn(
    'relative rounded-lg transition-all duration-200',
    'motion-reduce:transition-none',
    '[dir="rtl"]:space-reverse'
  );

  // Padding classes based on 8-point grid
  const paddingClasses = {
    none: '',
    sm: `p-${spacing['2']}`,
    md: `p-${spacing['4']}`,
    lg: `p-${spacing['8']}`,
    responsive: `p-${spacing['2']} sm:p-${spacing['4']} lg:p-${spacing['8']}`,
  };

  // Variant-specific styling
  const variantClasses = {
    default: cn(
      `bg-${colors.background.light} dark:bg-${colors.background.dark}`,
      `text-${colors.foreground.light} dark:text-${colors.foreground.dark}`,
      'border border-transparent'
    ),
    outline: cn(
      'bg-transparent',
      `border border-${colors.border.light} dark:border-${colors.border.dark}`
    ),
    ghost: cn(
      'bg-transparent',
      'border-none',
      `text-${colors.foreground.light} dark:text-${colors.foreground.dark}`
    ),
    elevated: cn(
      `bg-${colors.background.light} dark:bg-${colors.background.dark}`,
      'border border-transparent',
      'shadow-md dark:shadow-lg'
    ),
  };

  // Interactive state classes
  const interactiveClasses = interactive
    ? cn(
        'cursor-pointer',
        'hover:scale-[1.02]',
        'hover:shadow-lg',
        `active:bg-${colors.muted.light} dark:active:bg-${colors.muted.dark}`,
        'focus-visible:outline-none',
        `focus-visible:ring-2 focus-visible:ring-${colors.primary.light}`,
        'transition-transform duration-200'
      )
    : '';

  return cn(
    baseClasses,
    paddingClasses[padding],
    variantClasses[variant],
    interactiveClasses,
    className
  );
};

/**
 * Card component providing a consistent container with theme integration
 * and accessibility features
 */
export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  (
    {
      variant = 'default',
      padding = 'md',
      interactive = false,
      className,
      children,
      role = 'region',
      'aria-label': ariaLabel,
      ...props
    },
    ref
  ) => {
    // Generate combined class names
    const classes = getCardClasses({
      variant,
      padding,
      interactive,
      className,
    });

    return (
      <div
        ref={ref}
        role={role}
        aria-label={ariaLabel}
        tabIndex={interactive ? 0 : undefined}
        className={classes}
        {...props}
      >
        {children}
      </div>
    );
  }
);

// Display name for dev tools
Card.displayName = 'Card';

// Default props
Card.defaultProps = {
  variant: 'default',
  padding: 'md',
  interactive: false,
  role: 'region',
};

export default Card;