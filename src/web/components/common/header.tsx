"use client";

import React, { useState, useCallback, useEffect, useRef } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { cn } from 'class-variance-authority';
import Button from './button';
import SearchBar from './search-bar';
import LogoutButton from '../auth/logout-button';
import { useAuth } from '../../hooks/useAuth';

// Version: ^18.2.0 - react
// Version: ^13.0.0 - next/link, next/navigation
// Version: ^0.7.0 - class-variance-authority

/**
 * Header component variants using class-variance-authority
 */
const headerVariants = cn({
  base: [
    'w-full',
    'flex',
    'items-center',
    'justify-between',
    'px-4',
    'h-16',
    'transition-colors',
    'duration-200',
    'ease-in-out',
  ],
  variants: {
    layout: {
      default: 'bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800',
      transparent: 'bg-transparent'
    },
    position: {
      fixed: 'fixed top-0 left-0 right-0 z-50',
      relative: 'relative'
    }
  },
  defaultVariants: {
    layout: 'default',
    position: 'fixed'
  }
});

export interface HeaderProps {
  /** Additional CSS classes for styling */
  className?: string;
  /** Toggle search bar visibility */
  showSearch?: boolean;
  /** Toggle authentication controls visibility */
  showAuth?: boolean;
  /** Header layout variant */
  variant?: 'layout';
  /** Header position style */
  position?: 'fixed' | 'relative';
}

/**
 * Header Component
 * 
 * A responsive, accessible header component implementing the application's top navigation
 * with authentication state, search functionality, and theme switching capabilities.
 * Fully compliant with WCAG 2.1 AA standards.
 */
const Header = React.memo<HeaderProps>(({
  className,
  showSearch = true,
  showAuth = true,
  variant = 'default',
  position = 'fixed'
}) => {
  // Hooks
  const router = useRouter();
  const { state: { isAuthenticated, user }, checkPermission } = useAuth();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isSearchExpanded, setIsSearchExpanded] = useState(false);
  const headerRef = useRef<HTMLElement>(null);
  const searchRef = useRef<HTMLDivElement>(null);

  // Handle mobile menu toggle
  const toggleMobileMenu = useCallback(() => {
    setIsMobileMenuOpen(prev => !prev);
  }, []);

  // Handle search functionality
  const handleSearch = useCallback(async (query: string) => {
    try {
      const searchParams = new URLSearchParams({ q: query });
      router.push(`/search?${searchParams.toString()}`);
    } catch (error) {
      console.error('Search error:', error);
    }
  }, [router]);

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setIsMobileMenuOpen(false);
        setIsSearchExpanded(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Handle click outside for mobile menu
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        headerRef.current && 
        !headerRef.current.contains(e.target as Node) &&
        !searchRef.current?.contains(e.target as Node)
      ) {
        setIsMobileMenuOpen(false);
        setIsSearchExpanded(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header
      ref={headerRef}
      className={headerVariants({ layout: variant, position, className })}
      role="banner"
    >
      {/* Logo and Navigation */}
      <div className="flex items-center gap-4">
        <Link 
          href="/"
          className="flex items-center gap-2 font-semibold text-lg"
          aria-label="Home"
        >
          Transfer Requirements
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-4" role="navigation">
          {checkPermission('view_requirements') && (
            <Link 
              href="/requirements"
              className="text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white"
            >
              Requirements
            </Link>
          )}
          {checkPermission('view_student_data') && (
            <Link 
              href="/students"
              className="text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white"
            >
              Students
            </Link>
          )}
          {checkPermission('generate_reports') && (
            <Link 
              href="/reports"
              className="text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white"
            >
              Reports
            </Link>
          )}
        </nav>
      </div>

      {/* Search and Auth Controls */}
      <div className="flex items-center gap-4">
        {/* Search Bar */}
        {showSearch && (
          <div 
            ref={searchRef}
            className={cn(
              'transition-all duration-200',
              isSearchExpanded ? 'w-full md:w-96' : 'w-auto'
            )}
          >
            <SearchBar
              onSearch={handleSearch}
              placeholder="Search requirements..."
              className="w-full"
              showSuggestions
              type="requirements"
            />
          </div>
        )}

        {/* Authentication Controls */}
        {showAuth && (
          <div className="flex items-center gap-2">
            {isAuthenticated ? (
              <>
                <Button
                  variant="ghost"
                  size="sm"
                  className="hidden md:flex"
                  ariaLabel={`Logged in as ${user?.email}`}
                >
                  {user?.email}
                </Button>
                <LogoutButton
                  variant="outline"
                  size="sm"
                  className="hidden md:flex"
                />
              </>
            ) : (
              <Button
                variant="primary"
                size="sm"
                onClick={() => router.push('/login')}
                ariaLabel="Login"
              >
                Login
              </Button>
            )}
          </div>
        )}

        {/* Mobile Menu Button */}
        <Button
          variant="ghost"
          size="sm"
          className="md:hidden"
          onClick={toggleMobileMenu}
          ariaLabel={isMobileMenuOpen ? 'Close menu' : 'Open menu'}
          aria-expanded={isMobileMenuOpen}
        >
          <span className="sr-only">
            {isMobileMenuOpen ? 'Close menu' : 'Open menu'}
          </span>
          {/* Hamburger Icon */}
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            {isMobileMenuOpen ? (
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            ) : (
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 12h16M4 18h16"
              />
            )}
          </svg>
        </Button>
      </div>

      {/* Mobile Menu */}
      {isMobileMenuOpen && (
        <div
          className="absolute top-16 left-0 right-0 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 md:hidden"
          role="dialog"
          aria-label="Mobile menu"
        >
          <nav className="flex flex-col p-4 space-y-4">
            {checkPermission('view_requirements') && (
              <Link 
                href="/requirements"
                className="text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                Requirements
              </Link>
            )}
            {checkPermission('view_student_data') && (
              <Link 
                href="/students"
                className="text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                Students
              </Link>
            )}
            {checkPermission('generate_reports') && (
              <Link 
                href="/reports"
                className="text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                Reports
              </Link>
            )}
            {isAuthenticated && (
              <LogoutButton
                variant="outline"
                size="sm"
                className="w-full"
              />
            )}
          </nav>
        </div>
      )}
    </header>
  );
});

Header.displayName = 'Header';

export default Header;