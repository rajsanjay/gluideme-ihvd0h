"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu } from "lucide-react";
import { cn } from "class-variance-authority";
import { Button } from "../common/button";
import { ROUTE_PATHS } from "../../config/routes";
import { useAuth } from "../../hooks/useAuth";
import { ErrorBoundary } from "../common/error-boundary";

// Define navigation item interface with accessibility and role-based access
interface NavItem {
  label: string;
  path: string;
  icon: React.ReactNode;
  roles: string[];
  ariaLabel: string;
  requiresAuth: boolean;
}

// Props interface for the Sidebar component
interface SidebarProps {
  className?: string;
  isCollapsed?: boolean;
  onToggle?: () => void;
  ariaLabel?: string;
  role?: string;
}

/**
 * Generates role-filtered navigation items with memoization
 * @param role - Current user role
 * @param authState - Authentication state
 * @returns Filtered navigation items
 */
const getNavItems = React.useCallback((role: string | undefined, authState: any): NavItem[] => {
  const baseNavItems: NavItem[] = [
    {
      label: "Home",
      path: ROUTE_PATHS.HOME,
      icon: <span className="text-xl">🏠</span>,
      roles: ["*"],
      ariaLabel: "Navigate to home page",
      requiresAuth: false
    },
    {
      label: "Search",
      path: ROUTE_PATHS.SEARCH,
      icon: <span className="text-xl">🔍</span>,
      roles: ["*"],
      ariaLabel: "Search transfer requirements",
      requiresAuth: false
    },
    {
      label: "Dashboard",
      path: ROUTE_PATHS.DASHBOARD,
      icon: <span className="text-xl">📊</span>,
      roles: ["admin", "institution_admin"],
      ariaLabel: "Access administrator dashboard",
      requiresAuth: true
    },
    {
      label: "Requirements",
      path: ROUTE_PATHS.REQUIREMENTS,
      icon: <span className="text-xl">📝</span>,
      roles: ["admin", "institution_admin"],
      ariaLabel: "Manage transfer requirements",
      requiresAuth: true
    },
    {
      label: "Student Plan",
      path: ROUTE_PATHS.STUDENT,
      icon: <span className="text-xl">📚</span>,
      roles: ["student"],
      ariaLabel: "View your transfer plan",
      requiresAuth: true
    }
  ];

  // Filter items based on user role and authentication state
  return baseNavItems.filter(item => {
    if (item.requiresAuth && !authState.isAuthenticated) return false;
    if (item.roles.includes("*")) return true;
    return role && item.roles.includes(role);
  });
}, []);

/**
 * Enhanced route matching with nested route support
 */
const isActiveRoute = React.useCallback((path: string, currentPath: string): boolean => {
  if (path === ROUTE_PATHS.HOME) {
    return currentPath === path;
  }
  return currentPath.startsWith(path);
}, []);

/**
 * Sidebar Component
 * 
 * A responsive sidebar navigation component that implements role-based access control
 * and WCAG 2.1 AA compliance standards.
 */
const Sidebar: React.FC<SidebarProps> = ({
  className,
  isCollapsed = false,
  onToggle,
  ariaLabel = "Main navigation",
  role = "navigation"
}) => {
  // Get current route and authentication state
  const pathname = usePathname();
  const { state: authState, user } = useAuth();

  // Track mobile menu state
  const [isMobileMenuOpen, setIsMobileMenuOpen] = React.useState(false);

  // Get filtered navigation items based on user role
  const navItems = React.useMemo(() => 
    getNavItems(user?.role, authState),
    [user?.role, authState]
  );

  // Handle mobile menu toggle
  const handleMobileMenuToggle = React.useCallback(() => {
    setIsMobileMenuOpen(prev => !prev);
    onToggle?.();
  }, [onToggle]);

  // Base sidebar styles
  const sidebarClasses = cn(
    "flex flex-col h-full bg-white dark:bg-neutral-900",
    "border-r border-neutral-200 dark:border-neutral-800",
    "transition-all duration-300 ease-in-out",
    {
      "w-64": !isCollapsed,
      "w-16": isCollapsed,
      "fixed inset-y-0 left-0 z-50": true,
      "translate-x-0": isMobileMenuOpen,
      "-translate-x-full": !isMobileMenuOpen
    },
    className
  );

  return (
    <ErrorBoundary
      fallback={<div className="p-4">Navigation temporarily unavailable</div>}
    >
      {/* Mobile Menu Toggle */}
      <Button
        variant="ghost"
        size="sm"
        className="fixed top-4 left-4 md:hidden z-50"
        onClick={handleMobileMenuToggle}
        ariaLabel={isMobileMenuOpen ? "Close menu" : "Open menu"}
      >
        <Menu className="w-5 h-5" />
      </Button>

      {/* Sidebar Navigation */}
      <nav
        className={sidebarClasses}
        aria-label={ariaLabel}
        role={role}
      >
        {/* Navigation Items */}
        <div className="flex flex-col gap-2 p-4">
          {navItems.map((item) => (
            <Link
              key={item.path}
              href={item.path}
              aria-label={item.ariaLabel}
              aria-current={isActiveRoute(item.path, pathname) ? "page" : undefined}
            >
              <Button
                variant={isActiveRoute(item.path, pathname) ? "primary" : "ghost"}
                className={cn(
                  "w-full justify-start gap-3",
                  isCollapsed && "justify-center p-2"
                )}
                aria-label={isCollapsed ? item.ariaLabel : undefined}
              >
                {item.icon}
                {!isCollapsed && (
                  <span className="truncate">{item.label}</span>
                )}
              </Button>
            </Link>
          ))}
        </div>
      </nav>

      {/* Mobile Overlay */}
      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black/50 md:hidden z-40"
          aria-hidden="true"
          onClick={handleMobileMenuToggle}
        />
      )}
    </ErrorBoundary>
  );
};

export default Sidebar;