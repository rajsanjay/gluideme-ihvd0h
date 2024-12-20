"use client";

import React, { useCallback, useEffect, useRef } from 'react';
import { cn } from 'class-variance-authority';
import MainLayout from '../../components/layout/main-layout';

// Props interface for SearchLayout component
interface SearchLayoutProps {
  children: React.ReactNode;
  className?: string;
}

/**
 * SearchLayout Component
 * 
 * A specialized layout wrapper for search pages that implements responsive design,
 * accessibility features, and performance optimizations. Provides structural
 * consistency across search-related pages while maintaining WCAG 2.1 AA compliance.
 *
 * @version 1.0.0
 */
const SearchLayout = React.memo(({ children, className }: SearchLayoutProps) => {
  // Ref for search results announcements
  const announcerRef = useRef<HTMLDivElement>(null);
  
  // Track search container focus state
  const [isFocused, setIsFocused] = React.useState(false);

  /**
   * Handle keyboard navigation within search results
   */
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    // Handle search-specific keyboard shortcuts
    switch (event.key) {
      case '/':
        // Focus search input when forward slash is pressed
        if (!event.target || (event.target as HTMLElement).tagName !== 'INPUT') {
          event.preventDefault();
          const searchInput = document.querySelector<HTMLInputElement>('[role="searchbox"]');
          searchInput?.focus();
        }
        break;
      case 'Escape':
        // Clear focus when Escape is pressed
        if (isFocused) {
          event.preventDefault();
          (document.activeElement as HTMLElement)?.blur();
          setIsFocused(false);
        }
        break;
    }
  }, [isFocused]);

  /**
   * Set up keyboard event listeners
   */
  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown]);

  /**
   * Update document title for search context
   */
  useEffect(() => {
    document.title = 'Search Transfer Requirements';
    return () => {
      document.title = 'Transfer Requirements Management System';
    };
  }, []);

  return (
    <MainLayout
      className={cn(
        'min-h-screen bg-background',
        'transition-colors duration-200',
        className
      )}
    >
      {/* Search content wrapper */}
      <div
        className={cn(
          'flex-1 px-4 py-6 md:px-6 lg:px-8',
          'relative isolate',
          'transition-all duration-200 ease-in-out',
          isFocused && 'bg-accent/5'
        )}
        role="search"
        aria-label="Search transfer requirements"
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
      >
        {/* Live region for search announcements */}
        <div
          ref={announcerRef}
          className="sr-only"
          role="status"
          aria-live="polite"
          aria-atomic="true"
        />

        {/* Search content area */}
        <div className={cn(
          'container mx-auto',
          'space-y-6',
          'animate-in fade-in-0 slide-in-from-bottom-2'
        )}>
          {/* Keyboard shortcut hint */}
          <div className="text-sm text-muted-foreground text-center">
            <kbd className="px-2 py-1 bg-muted rounded">
              Press / to focus search
            </kbd>
          </div>

          {/* Main search content */}
          {children}
        </div>
      </div>
    </MainLayout>
  );
});

// Set display name for debugging
SearchLayout.displayName = 'SearchLayout';

export default SearchLayout;