"use client";

import React, { useCallback, useEffect, useState } from 'react';
import { cn } from 'class-variance-authority';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import Button from '../common/button';
import SearchBar from '../common/search-bar';
import LogoutButton from '../auth/logout-button';
import { useAuth } from '../../hooks/useAuth';
import type { SearchType } from '../../types/search';

// Header component variants using class-variance-authority
const headerVariants = cn({
  base: [
    'sticky',
    'top-0',
    'z-50',
    'w-full',
    'border-b',
    'transition-colors',
    'duration-200'
  ],
  variants: {
    theme: {
      light: 'bg-white border-gray-200',
      dark: 'bg-gray-900 border-gray-800'
    },
    layout: {
      desktop: 'px-8 py-4',
      tablet: 'px-6 py-3',
      mobile: 'px-4 py-2'
    }
  },
  defaultVariants: {
    theme: 'light',
    layout: 'desktop'
  }
});

// Navigation item interface
interface NavigationItem {
  label: string;
  href: string;
  roles: string[];
  icon?: React.ReactNode;
  shortcut?: string;
}

export interface HeaderProps {
  className?: string;
  theme?: 'light' | 'dark';
  onThemeChange?: (theme: 'light' | 'dark') => void;
}

/**
 * Header Component
 * 
 * A responsive header component implementing the application's main navigation,
 * search functionality, and user controls. Supports theme switching and
 * role-based navigation items.
 */
const Header: React.FC<HeaderProps> = ({
  className,
  theme = 'light',
  onThemeChange
}) => {
  const router = useRouter();
  const { state: authState, isAuthenticated, user, logout } = useAuth();
  const [isMobile, setIsMobile] = useState(false);

  // Handle responsive layout
  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
    };

    handleResize();
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  // Get navigation items based on user role
  const getNavigationItems = useCallback((): NavigationItem[] => {
    const baseItems: NavigationItem[] = [
      {
        label: 'Requirements',
        href: '/requirements',
        roles: ['admin', 'institution_admin', 'counselor', 'student', 'guest'],
        shortcut: 'Alt+R'
      },
      {
        label: 'Search',
        href: '/search',
        roles: ['admin', 'institution_admin', 'counselor', 'student', 'guest'],
        shortcut: 'Alt+S'
      }
    ];

    // Add role-specific items
    if (user?.role === 'admin' || user?.role === 'institution_admin') {
      baseItems.push({
        label: 'Management',
        href: '/management',
        roles: ['admin', 'institution_admin'],
        shortcut: 'Alt+M'
      });
    }

    if (user?.role === 'counselor') {
      baseItems.push({
        label: 'Student Plans',
        href: '/student-plans',
        roles: ['counselor'],
        shortcut: 'Alt+P'
      });
    }

    return baseItems;
  }, [user?.role]);

  // Handle search functionality
  const handleSearch = useCallback(async (query: string, type: SearchType = 'requirements') => {
    const searchParams = new URLSearchParams({
      q: query,
      type
    });
    router.push(`/search?${searchParams.toString()}`);
  }, [router]);

  // Handle theme toggle
  const handleThemeToggle = useCallback(() => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    onThemeChange?.(newTheme);
  }, [theme, onThemeChange]);

  return (
    <header
      className={cn(
        headerVariants({
          theme,
          layout: isMobile ? 'mobile' : 'desktop'
        }),
        className
      )}
      role="banner"
    >
      <div className="flex items-center justify-between">
        {/* Logo and Navigation */}
        <div className="flex items-center space-x-8">
          <Link href="/" className="flex items-center space-x-2">
            <span className="text-xl font-bold">
              Transfer Requirements
            </span>
          </Link>

          {/* Navigation Items */}
          {!isMobile && (
            <nav className="hidden md:flex items-center space-x-4" role="navigation">
              {getNavigationItems().map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    'px-3 py-2 rounded-md text-sm font-medium transition-colors',
                    'hover:bg-gray-100 dark:hover:bg-gray-800'
                  )}
                  accessKey={item.shortcut?.split('+')[1].toLowerCase()}
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          )}
        </div>

        {/* Search and User Controls */}
        <div className="flex items-center space-x-4">
          <div className="w-64 lg:w-96">
            <SearchBar
              onSearch={handleSearch}
              placeholder="Search requirements..."
              type="requirements"
              showSuggestions
              className="w-full"
            />
          </div>

          <div className="flex items-center space-x-2">
            {/* Theme Toggle */}
            <Button
              variant="ghost"
              size="sm"
              onClick={handleThemeToggle}
              ariaLabel={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`}
            >
              {theme === 'light' ? '🌙' : '☀️'}
            </Button>

            {/* Authentication Controls */}
            {isAuthenticated ? (
              <div className="flex items-center space-x-2">
                <span className="text-sm">
                  {user?.email}
                </span>
                <LogoutButton
                  variant="ghost"
                  size="sm"
                  onLogoutSuccess={() => router.push('/login')}
                />
              </div>
            ) : (
              <Button
                variant="primary"
                size="sm"
                onClick={() => router.push('/login')}
              >
                Login
              </Button>
            )}

            {/* Mobile Menu Button */}
            {isMobile && (
              <Button
                variant="ghost"
                size="sm"
                ariaLabel="Open menu"
                className="md:hidden"
              >
                ☰
              </Button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;