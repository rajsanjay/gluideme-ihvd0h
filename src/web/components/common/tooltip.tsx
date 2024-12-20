/**
 * @file Tooltip Component
 * @version 1.0.0
 * @description A reusable tooltip component providing contextual information with WCAG 2.1 AA compliance,
 * keyboard support, and RTL layout compatibility.
 * 
 * @requires react ^18.0.0
 * @requires @shadcn/ui ^0.1.0
 */

import React, { useState, useEffect, useCallback, useRef, useId } from 'react';
import { cn } from '@shadcn/ui';
import { colors, spacing } from '../../config/theme';

// Position type for tooltip placement
type TooltipPosition = 'top' | 'right' | 'bottom' | 'left';

// Interface for tooltip component props
export interface TooltipProps {
  /** Content to display in the tooltip */
  content: string | React.ReactNode;
  /** Element that triggers the tooltip */
  children: React.ReactNode;
  /** Position of the tooltip relative to the trigger element */
  position?: TooltipPosition;
  /** Delay before showing tooltip (ms) */
  delay?: number;
  /** Optional custom className for styling */
  className?: string;
}

/**
 * Calculates tooltip position based on trigger element and desired placement
 */
const calculatePosition = (
  triggerRect: DOMRect,
  tooltipRect: DOMRect,
  position: TooltipPosition,
  isRTL: boolean
): { top: number; left: number } => {
  const gap = parseInt(spacing['2'], 10);
  let top = 0;
  let left = 0;

  switch (position) {
    case 'top':
      top = triggerRect.top - tooltipRect.height - gap;
      left = triggerRect.left + (triggerRect.width - tooltipRect.width) / 2;
      break;
    case 'bottom':
      top = triggerRect.bottom + gap;
      left = triggerRect.left + (triggerRect.width - tooltipRect.width) / 2;
      break;
    case 'left':
      top = triggerRect.top + (triggerRect.height - tooltipRect.height) / 2;
      left = isRTL ? triggerRect.right + gap : triggerRect.left - tooltipRect.width - gap;
      break;
    case 'right':
      top = triggerRect.top + (triggerRect.height - tooltipRect.height) / 2;
      left = isRTL ? triggerRect.left - tooltipRect.width - gap : triggerRect.right + gap;
      break;
  }

  return { top, left };
};

/**
 * Tooltip component that provides contextual information with accessibility support
 */
const Tooltip: React.FC<TooltipProps> = ({
  content,
  children,
  position = 'top',
  delay = 200,
  className
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [coords, setCoords] = useState({ top: 0, left: 0 });
  const triggerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout>();
  const tooltipId = useId();

  // Check for RTL layout
  const isRTL = document.dir === 'rtl';

  /**
   * Updates tooltip position based on trigger element
   */
  const updatePosition = useCallback(() => {
    if (triggerRef.current && tooltipRef.current && isVisible) {
      const triggerRect = triggerRef.current.getBoundingClientRect();
      const tooltipRect = tooltipRef.current.getBoundingClientRect();
      const { top, left } = calculatePosition(triggerRect, tooltipRect, position, isRTL);
      setCoords({ top: top + window.scrollY, left: left + window.scrollX });
    }
  }, [position, isVisible, isRTL]);

  // Handle show/hide with delay
  const showTooltip = useCallback(() => {
    timeoutRef.current = setTimeout(() => setIsVisible(true), delay);
  }, [delay]);

  const hideTooltip = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setIsVisible(false);
  }, []);

  // Handle keyboard interactions
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (event.key === 'Escape' && isVisible) {
      hideTooltip();
    }
  }, [hideTooltip, isVisible]);

  // Set up event listeners
  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    window.addEventListener('resize', updatePosition);
    window.addEventListener('scroll', updatePosition);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('resize', updatePosition);
      window.removeEventListener('scroll', updatePosition);
    };
  }, [handleKeyDown, updatePosition]);

  // Update position when visibility changes
  useEffect(() => {
    if (isVisible) {
      updatePosition();
    }
  }, [isVisible, updatePosition]);

  return (
    <>
      <div
        ref={triggerRef}
        onMouseEnter={showTooltip}
        onMouseLeave={hideTooltip}
        onFocus={showTooltip}
        onBlur={hideTooltip}
        aria-describedby={tooltipId}
        className="inline-block"
      >
        {children}
      </div>
      {isVisible && (
        <div
          ref={tooltipRef}
          id={tooltipId}
          role="tooltip"
          className={cn(
            'fixed z-50 px-3 py-2 text-sm rounded shadow-md',
            'bg-background text-foreground',
            'animate-in fade-in-0 zoom-in-95',
            'dark:bg-secondary dark:text-foreground',
            className
          )}
          style={{
            top: coords.top,
            left: coords.left,
            maxWidth: '20rem',
            ...(!isRTL ? { direction: 'ltr' } : { direction: 'rtl' })
          }}
        >
          {content}
        </div>
      )}
    </>
  );
};

export default Tooltip;