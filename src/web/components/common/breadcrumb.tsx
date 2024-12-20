"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTranslation } from "next-i18next";
import { ChevronRight } from "lucide-react";
import { cva } from "class-variance-authority";
import { ROUTE_PATHS, generatePath } from "../../config/routes";
import { Button, buttonVariants } from "./button";

// Version: ^18.2.0 - react
// Version: ^13.0.0 - next
// Version: ^13.0.0 - next-i18next
// Version: ^0.284.0 - lucide-react
// Version: ^0.7.0 - class-variance-authority

/**
 * Style variants for the breadcrumb component using class-variance-authority
 */
export const breadcrumbVariants = cva({
  base: "flex items-center space-x-2 text-sm text-neutral-600 dark:text-neutral-300 focus-within:outline-none",
  variants: {
    separator: "text-neutral-400 dark:text-neutral-500 select-none",
    item: {
      default: "hover:text-neutral-900 dark:hover:text-white transition-colors focus:ring-2 focus:ring-primary-500 rounded px-2 py-1",
      active: "text-neutral-900 dark:text-white font-medium cursor-default aria-[current]:font-bold"
    },
    container: "nav relative",
    list: "flex items-center list-none p-0 m-0"
  }
});

/**
 * Interface for breadcrumb navigation items
 */
export interface BreadcrumbItem {
  label: string;
  href: string;
  isActive?: boolean;
  metadata?: Record<string, unknown>;
  ariaLabel?: string;
  testId?: string;
}

/**
 * Props interface for Breadcrumb component
 */
export interface BreadcrumbProps {
  items: BreadcrumbItem[];
  className?: string;
  separator?: React.ReactNode;
  maxItems?: number;
  showHome?: boolean;
  onNavigate?: (item: BreadcrumbItem) => void;
  testId?: string;
}

/**
 * Options for the useBreadcrumbs hook
 */
interface UseBreadcrumbsOptions {
  showHome?: boolean;
  maxItems?: number;
}

/**
 * Custom hook for generating breadcrumb items with metadata
 */
export function useBreadcrumbs(options: UseBreadcrumbsOptions = {}): BreadcrumbItem[] {
  const { showHome = true, maxItems } = options;
  const pathname = usePathname();
  const { t } = useTranslation();

  return React.useMemo(() => {
    const segments = pathname
      .split("/")
      .filter(Boolean)
      .map((segment, index, array) => {
        const path = `/${array.slice(0, index + 1).join("/")}`;
        const isActive = index === array.length - 1;

        // Generate label based on route or parameter
        const label = segment.startsWith("[") && segment.endsWith("]")
          ? t(`breadcrumbs.dynamic.${segment.slice(1, -1)}`)
          : t(`breadcrumbs.static.${segment}`);

        return {
          label,
          href: path,
          isActive,
          ariaLabel: t(`breadcrumbs.aria.${segment}`, { defaultValue: label }),
          testId: `breadcrumb-${segment}`
        };
      });

    // Add home item if enabled
    const items = showHome
      ? [
          {
            label: t("breadcrumbs.home"),
            href: ROUTE_PATHS.HOME,
            ariaLabel: t("breadcrumbs.aria.home"),
            testId: "breadcrumb-home"
          },
          ...segments
        ]
      : segments;

    // Limit items if maxItems is specified
    return maxItems && items.length > maxItems
      ? [
          items[0],
          { label: "...", href: "", testId: "breadcrumb-ellipsis" },
          ...items.slice(-maxItems + 2)
        ]
      : items;
  }, [pathname, showHome, maxItems, t]);
}

/**
 * Breadcrumb Component
 * 
 * A production-ready breadcrumb navigation component that provides hierarchical
 * page location awareness. Supports internationalization, keyboard navigation,
 * and screen reader accessibility.
 */
const Breadcrumb: React.FC<BreadcrumbProps> = ({
  items,
  className,
  separator = <ChevronRight className="h-4 w-4" aria-hidden="true" />,
  maxItems,
  showHome = true,
  onNavigate,
  testId = "breadcrumb-nav"
}) => {
  // Handle keyboard navigation
  const handleKeyDown = React.useCallback(
    (event: React.KeyboardEvent, item: BreadcrumbItem) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        onNavigate?.(item);
      }
    },
    [onNavigate]
  );

  return (
    <nav
      aria-label="Breadcrumb"
      className={breadcrumbVariants({ className })}
      data-testid={testId}
    >
      <ol className={breadcrumbVariants({ variant: "list" })} role="list">
        {items.map((item, index) => (
          <li
            key={item.href || index}
            className="flex items-center"
            data-testid={item.testId}
          >
            {index > 0 && (
              <span
                className={breadcrumbVariants({ variant: "separator" })}
                aria-hidden="true"
              >
                {separator}
              </span>
            )}
            
            {item.isActive ? (
              <span
                className={breadcrumbVariants({ variant: "item", active: true })}
                aria-current="page"
              >
                {item.label}
              </span>
            ) : (
              <Link
                href={item.href}
                className={buttonVariants({
                  variant: "ghost",
                  size: "sm",
                  className: breadcrumbVariants({ variant: "item" })
                })}
                onClick={() => onNavigate?.(item)}
                onKeyDown={(e) => handleKeyDown(e, item)}
                aria-label={item.ariaLabel}
              >
                {item.label}
              </Link>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
};

// Set display name for dev tools
Breadcrumb.displayName = "Breadcrumb";

export default Breadcrumb;