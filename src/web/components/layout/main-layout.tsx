"use client";

import React, { useCallback, useEffect, useState } from 'react';
import { cn } from 'class-variance-authority';
import { useMediaQuery } from '@react-hook/media-query';
import { Header } from './header';
import { Footer } from './footer';
import { Sidebar } from './sidebar';
import { useAuth } from '../../hooks/useAuth';
import { ErrorBoundary } from '../common/error-boundary';

// Layout component props interface
export interface MainLayoutProps {
  children: React.ReactNode;
  className?: string;
}

/**
 * MainLayout Component
 * 
 * A core layout component that implements the application's main structure with
 * responsive header, sidebar, content area and footer. Implements WCAG 2.1 AA
 * compliance and handles layout adaptations for different screen sizes and user roles.
 */
const MainLayout: React.FC<MainLayoutProps> = ({
  children,
  className
}) => {
  // Get authentication state
  const { state: authState } = useAuth();

  // Track sidebar collapse state
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(() => {
    // Initialize from localStorage if available
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('sidebarCollapsed');
      return stored ? JSON.parse(stored) : false;
    }
    return false;
  });

  // Track theme state
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('theme') as 'light' | 'dark' || 'light';
    }
    return 'light';
  });

  // Media queries for responsive behavior
  const isMobile = useMediaQuery('(max-width: 768px)');
  const isTablet = useMediaQuery('(min-width: 769px) and (max-width: 1024px)');

  /**
   * Handle sidebar toggle with persistence
   */
  const handleSidebarToggle = useCallback(() => {
    setIsSidebarCollapsed(prev => {
      const newState = !prev;
      localStorage.setItem('sidebarCollapsed', JSON.stringify(newState));
      return newState;
    });
  }, []);

  /**
   * Handle theme changes with persistence
   */
  const handleThemeChange = useCallback((newTheme: 'light' | 'dark') => {
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    document.documentElement.classList.toggle('dark', newTheme === 'dark');
  }, []);

  /**
   * Handle keyboard navigation
   */
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    // Toggle sidebar with keyboard shortcut
    if (event.altKey && event.key === 'b') {
      handleSidebarToggle();
    }

    // Toggle theme with keyboard shortcut
    if (event.altKey && event.key === 't') {
      handleThemeChange(theme === 'light' ? 'dark' : 'light');
    }
  }, [handleSidebarToggle, handleThemeChange, theme]);

  // Set up keyboard listeners and initialize theme
  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    document.documentElement.classList.toggle('dark', theme === 'dark');

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown, theme]);

  return (
    <ErrorBoundary
      fallback={
        <div className="flex min-h-screen flex-col items-center justify-center p-4">
          <h1 className="text-xl font-semibold">Something went wrong</h1>
          <p className="mt-2 text-gray-600">Please try refreshing the page</p>
        </div>
      }
    >
      <div className={cn(
        'min-h-screen flex flex-col',
        theme === 'dark' ? 'dark' : '',
        className
      )}>
        {/* Skip link for keyboard navigation */}
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:p-4 focus:bg-white focus:text-black"
        >
          Skip to main content
        </a>

        {/* Header */}
        <Header
          theme={theme}
          onThemeChange={handleThemeChange}
          className="z-50"
        />

        {/* Main content area with sidebar */}
        <div className="flex-1 flex">
          {/* Sidebar - hidden on mobile unless explicitly opened */}
          {!isMobile && (
            <Sidebar
              isCollapsed={isSidebarCollapsed}
              onToggle={handleSidebarToggle}
              className={cn(
                'transition-all duration-300',
                isSidebarCollapsed ? 'w-16' : 'w-64'
              )}
            />
          )}

          {/* Main content */}
          <main
            id="main-content"
            className={cn(
              'flex-1 p-6',
              'transition-all duration-300',
              isMobile ? 'w-full' : 'ml-0'
            )}
            role="main"
            aria-label="Main content"
          >
            <ErrorBoundary
              fallback={
                <div className="p-4 border border-red-200 rounded bg-red-50">
                  <h2 className="text-lg font-semibold text-red-800">
                    Content Error
                  </h2>
                  <p className="mt-2 text-red-600">
                    There was an error loading this content.
                  </p>
                </div>
              }
            >
              {children}
            </ErrorBoundary>
          </main>
        </div>

        {/* Footer */}
        <Footer className="mt-auto" />
      </div>
    </ErrorBoundary>
  );
};

export default MainLayout;