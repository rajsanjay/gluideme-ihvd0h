// @version React ^18.0.0
// @version class-variance-authority ^0.7.0
// @version next/router ^13.0.0
// @version focus-trap-react ^11.0.0
// @version @mantine/hooks ^7.0.0

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/router';
import { cn } from 'class-variance-authority';
import FocusTrap from 'focus-trap-react';
import { useMediaQuery } from '@mantine/hooks';
import { ROUTE_PATHS } from '../../config/routes';

// Constants for touch interactions and animations
const SWIPE_THRESHOLD = 50;
const TRANSITION_CLASS = 'transition-transform ease-in-out';

/**
 * Props interface for the Sidebar component with comprehensive type safety
 */
interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  onStateChange?: (state: boolean) => void;
  children: React.ReactNode;
  className?: string;
  ariaLabel?: string;
  transitionDuration?: number;
}

/**
 * Enhanced sidebar component with accessibility and performance optimizations
 * Implements WCAG 2.1 AA compliance and responsive behavior
 */
const Sidebar: React.FC<SidebarProps> = ({
  isOpen,
  onClose,
  onStateChange,
  children,
  className,
  ariaLabel = 'Navigation Sidebar',
  transitionDuration = 200,
}) => {
  const router = useRouter();
  const sidebarRef = useRef<HTMLDivElement>(null);
  const touchStartX = useRef<number>(0);
  const [isAnimating, setIsAnimating] = useState(false);
  const isMobile = useMediaQuery('(max-width: 1024px)');

  // Dynamic class generation for different states
  const sidebarClasses = cn(
    // Base styles with 8-point grid system
    'flex flex-col h-full bg-background border-r border-border focus-visible:outline-none',
    // Responsive layout
    'fixed lg:static inset-y-0 left-0 z-50 w-64',
    // Animation states
    {
      [TRANSITION_CLASS]: isAnimating,
      'translate-x-0 shadow-lg': isOpen,
      '-translate-x-full lg:translate-x-0': !isOpen,
    },
    // Touch interaction styles
    'touch-pan-y touch-pan-x',
    className
  );

  // Handle transition end to clean up animation state
  const handleTransitionEnd = useCallback(() => {
    setIsAnimating(false);
  }, []);

  // Touch event handlers for mobile swipe
  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartX.current = e.touches[0].clientX;
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (!isMobile) return;

    const touchCurrentX = e.touches[0].clientX;
    const diff = touchStartX.current - touchCurrentX;

    if (isOpen && diff > SWIPE_THRESHOLD) {
      setIsAnimating(true);
      onClose();
    }
  };

  // Keyboard event handlers for accessibility
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape' && isOpen && isMobile) {
      onClose();
    }
  };

  // Route change handler for mobile view
  useEffect(() => {
    const handleRouteChange = () => {
      if (isMobile && isOpen) {
        onClose();
      }
    };

    router.events.on('routeChangeStart', handleRouteChange);
    return () => {
      router.events.off('routeChangeStart', handleRouteChange);
    };
  }, [router, isMobile, isOpen, onClose]);

  // Notify parent of state changes
  useEffect(() => {
    onStateChange?.(isOpen);
  }, [isOpen, onStateChange]);

  // Handle body scroll lock on mobile
  useEffect(() => {
    if (isMobile) {
      document.body.style.overflow = isOpen ? 'hidden' : '';
      return () => {
        document.body.style.overflow = '';
      };
    }
  }, [isMobile, isOpen]);

  // Render different content based on viewport
  const sidebarContent = (
    <nav
      ref={sidebarRef}
      className={sidebarClasses}
      aria-label={ariaLabel}
      role="navigation"
      style={{ transitionDuration: `${transitionDuration}ms` }}
      onKeyDown={handleKeyDown}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTransitionEnd={handleTransitionEnd}
      data-testid="sidebar"
    >
      {/* Close button for mobile view */}
      {isMobile && isOpen && (
        <button
          className="lg:hidden absolute right-4 top-4 p-2 rounded-md hover:bg-accent focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
          onClick={onClose}
          aria-label="Close sidebar"
        >
          <span className="sr-only">Close sidebar</span>
          <svg
            className="h-6 w-6"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      )}

      {/* Main content with lazy loading optimization */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden px-4 py-6">
        {children}
      </div>
    </nav>
  );

  // Wrap with FocusTrap only on mobile
  return isMobile ? (
    <FocusTrap
      active={isOpen}
      focusTrapOptions={{
        allowOutsideClick: true,
        clickOutsideDeactivates: true,
        initialFocus: false,
      }}
    >
      {sidebarContent}
    </FocusTrap>
  ) : (
    sidebarContent
  );
};

// Memoize the component for performance
export default React.memo(Sidebar);

// Export type for external usage
export type { SidebarProps };