/**
 * @file Navigation Component
 * @version 1.0.0
 * @description Enterprise-grade navigation component implementing role-based access control,
 * responsive behavior, accessibility compliance, and advanced features.
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'next-i18next'; // ^13.0.0
import { useMediaQuery } from '@mantine/hooks'; // ^6.0.0
import { useAnalytics } from '@analytics/react'; // ^0.1.0
import { Button } from '../common/button';
import { Dropdown } from '../common/dropdown';
import { ErrorBoundary } from '../common/error-boundary';
import { Toast } from '../common/toast';

// Navigation item interface with enhanced type safety
interface NavItem {
  label: string;
  path: string;
  icon?: React.ReactNode;
  badge?: {
    text: string;
    variant: 'primary' | 'warning' | 'error';
  };
  permissionKey: string;
  subItems?: NavItem[];
  analyticsId: string;
}

// Props interface with comprehensive configuration options
interface NavigationProps {
  className?: string;
  onNavigate?: (path: string) => void;
  customTheme?: NavigationTheme;
  testId?: string;
}

// Theme configuration interface
interface NavigationTheme {
  backgroundColor: string;
  textColor: string;
  activeColor: string;
  hoverColor: string;
}

// Default theme configuration
const defaultTheme: NavigationTheme = {
  backgroundColor: 'bg-white dark:bg-gray-800',
  textColor: 'text-gray-700 dark:text-gray-200',
  activeColor: 'text-primary-600 dark:text-primary-400',
  hoverColor: 'hover:bg-gray-100 dark:hover:bg-gray-700'
};

/**
 * Custom hook for managing navigation items with role-based access control
 */
const useNavigationItems = (role: string, permissions: string[]) => {
  return useMemo(() => {
    const items: NavItem[] = [
      {
        label: 'Dashboard',
        path: '/dashboard',
        permissionKey: 'view:dashboard',
        analyticsId: 'nav_dashboard'
      },
      {
        label: 'Transfer Requirements',
        path: '/requirements',
        permissionKey: 'view:requirements',
        analyticsId: 'nav_requirements',
        subItems: [
          {
            label: 'Search',
            path: '/requirements/search',
            permissionKey: 'view:requirements',
            analyticsId: 'nav_requirements_search'
          },
          {
            label: 'Manage',
            path: '/requirements/manage',
            permissionKey: 'manage:requirements',
            analyticsId: 'nav_requirements_manage'
          }
        ]
      },
      {
        label: 'Institutions',
        path: '/institutions',
        permissionKey: 'view:institutions',
        analyticsId: 'nav_institutions'
      },
      {
        label: 'Reports',
        path: '/reports',
        permissionKey: 'view:reports',
        analyticsId: 'nav_reports',
        badge: {
          text: 'New',
          variant: 'primary'
        }
      }
    ];

    // Filter items based on user permissions
    return items.filter(item => {
      const hasPermission = permissions.includes(item.permissionKey);
      if (item.subItems) {
        item.subItems = item.subItems.filter(subItem => 
          permissions.includes(subItem.permissionKey)
        );
      }
      return hasPermission;
    });
  }, [role, permissions]);
};

/**
 * Custom hook for navigation analytics
 */
const useNavigationAnalytics = () => {
  const analytics = useAnalytics();

  return useCallback((analyticsId: string, path: string) => {
    analytics.track('navigation_click', {
      id: analyticsId,
      path,
      timestamp: new Date().toISOString()
    });
  }, [analytics]);
};

/**
 * Enterprise-grade Navigation component
 */
export const Navigation: React.FC<NavigationProps> = ({
  className,
  onNavigate,
  customTheme = defaultTheme,
  testId = 'navigation'
}) => {
  const { t } = useTranslation('common');
  const isMobile = useMediaQuery('(max-width: 768px)');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);
  
  // Simulated user role and permissions - replace with actual auth context
  const role = 'admin';
  const permissions = ['view:dashboard', 'view:requirements', 'manage:requirements', 'view:institutions', 'view:reports'];

  const navigationItems = useNavigationItems(role, permissions);
  const trackNavigation = useNavigationAnalytics();

  // Handle navigation with analytics tracking
  const handleNavigate = useCallback((item: NavItem) => {
    trackNavigation(item.analyticsId, item.path);
    onNavigate?.(item.path);
    setIsMobileMenuOpen(false);
  }, [onNavigate, trackNavigation]);

  // Handle keyboard navigation
  const handleKeyDown = useCallback((event: React.KeyboardEvent, item: NavItem) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleNavigate(item);
    }
  }, [handleNavigate]);

  // Close mobile menu on resize
  useEffect(() => {
    if (!isMobile && isMobileMenuOpen) {
      setIsMobileMenuOpen(false);
    }
  }, [isMobile, isMobileMenuOpen]);

  return (
    <ErrorBoundary
      fallback={
        <div className="p-4 text-red-500">
          {t('navigation.error')}
        </div>
      }
    >
      <nav
        className={`${customTheme.backgroundColor} ${className}`}
        data-testid={testId}
        role="navigation"
        aria-label={t('navigation.main')}
      >
        {/* Mobile Menu Button */}
        {isMobile && (
          <Button
            aria-expanded={isMobileMenuOpen}
            aria-controls="mobile-menu"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="md:hidden"
            aria-label={t(isMobileMenuOpen ? 'navigation.close' : 'navigation.open')}
          >
            <span className="sr-only">
              {t(isMobileMenuOpen ? 'navigation.close' : 'navigation.open')}
            </span>
            {/* Menu icon */}
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
        )}

        {/* Navigation Items */}
        <ul
          className={`${
            isMobile
              ? `${isMobileMenuOpen ? 'block' : 'hidden'} mt-2`
              : 'flex items-center space-x-4'
          }`}
          id="mobile-menu"
        >
          {navigationItems.map((item) => (
            <li key={item.path} className="relative">
              {item.subItems ? (
                <Dropdown
                  options={item.subItems.map(subItem => ({
                    value: subItem.path,
                    label: t(subItem.label),
                    disabled: false
                  }))}
                  value=""
                  onChange={(value) => {
                    const subItem = item.subItems?.find(si => si.path === value);
                    if (subItem) {
                      handleNavigate(subItem);
                    }
                  }}
                  className={`${customTheme.textColor} ${customTheme.hoverColor}`}
                />
              ) : (
                <Button
                  variant="ghost"
                  className={`${customTheme.textColor} ${customTheme.hoverColor}`}
                  onClick={() => handleNavigate(item)}
                  onKeyDown={(e) => handleKeyDown(e, item)}
                  aria-current={item.path === window.location.pathname ? 'page' : undefined}
                >
                  {item.icon && <span className="mr-2">{item.icon}</span>}
                  {t(item.label)}
                  {item.badge && (
                    <span className={`ml-2 px-2 py-1 text-xs rounded-full bg-${item.badge.variant}-100 text-${item.badge.variant}-800`}>
                      {item.badge.text}
                    </span>
                  )}
                </Button>
              )}
            </li>
          ))}
        </ul>
      </nav>
    </ErrorBoundary>
  );
};

export default Navigation;