/**
 * @fileoverview Enhanced requirement list component with virtualization, accessibility,
 * and comprehensive filtering capabilities
 * @version 1.0.0
 */

import * as React from 'react';
import { cn } from '@shadcn/ui'; // v0.1.0
import { useVirtualizer } from '@tanstack/virtual'; // v3.0.0
import { useIntersectionObserver } from '@hooks/intersection-observer'; // v1.0.0
import { RequirementCard } from './requirement-card';
import { useRequirements } from '../../hooks/useRequirements';
import { LoadingSpinner } from '../common/loading-spinner';
import type { TransferRequirement } from '../../types/requirements';
import { ErrorBoundary } from '../common/error-boundary';
import { useToast } from '../../hooks/useToast';

/**
 * Props interface for the RequirementList component
 */
interface RequirementListProps {
  /** Callback for requirement selection */
  onRequirementClick: (id: string) => void;
  /** Additional CSS classes */
  className?: string;
  /** Display mode for requirements */
  viewType: 'grid' | 'list';
  /** Number of items per page */
  pageSize?: number;
  /** Filter options for requirements */
  filters?: Record<string, unknown>;
  /** Sort configuration */
  sortBy?: string;
  /** Enable virtual scrolling for large lists */
  virtualScroll?: boolean;
}

/**
 * Constants for layout and virtualization
 */
const GRID_BREAKPOINTS = {
  sm: 1,
  md: 2,
  lg: 3,
  xl: 4,
} as const;

const ITEM_SIZE = {
  list: 120,
  grid: 280,
} as const;

/**
 * Enhanced requirement list component with virtualization support
 */
export const RequirementList = React.memo<RequirementListProps>(({
  onRequirementClick,
  className,
  viewType = 'grid',
  pageSize = 10,
  filters = {},
  sortBy,
  virtualScroll = true,
}) => {
  // Container ref for virtualization
  const containerRef = React.useRef<HTMLDivElement>(null);
  
  // Toast notifications
  const toast = useToast();

  // Requirements data hook
  const {
    requirements,
    isLoading,
    error,
    total,
    updatePagination,
    updateFilters,
    updateSort,
  } = useRequirements({
    pagination: { page: 1, pageSize },
    filters,
    sort: { sortBy, direction: 'desc' },
  });

  // Virtual list configuration
  const rowVirtualizer = React.useMemo(
    () => virtualScroll && containerRef.current
      ? useVirtualizer({
          count: total,
          getScrollElement: () => containerRef.current,
          estimateSize: () => viewType === 'list' ? ITEM_SIZE.list : ITEM_SIZE.grid,
          overscan: 5,
        })
      : null,
    [total, viewType, virtualScroll]
  );

  // Intersection observer for infinite scroll
  const { ref: intersectionRef } = useIntersectionObserver({
    threshold: 0.5,
    onIntersect: () => {
      if (!isLoading && requirements.length < total) {
        updatePagination({ page: Math.ceil(requirements.length / pageSize) + 1, pageSize });
      }
    },
  });

  /**
   * Enhanced click handler with analytics tracking
   */
  const handleRequirementClick = React.useCallback((id: string) => {
    try {
      onRequirementClick(id);
      // Track click event (analytics implementation)
      console.info('Requirement clicked:', id);
    } catch (error) {
      toast.show({
        message: 'Failed to process requirement selection',
        type: 'error',
      });
    }
  }, [onRequirementClick, toast]);

  /**
   * Renders the list of requirements with virtualization support
   */
  const renderRequirements = () => {
    if (error) {
      return (
        <div className="p-4 text-center text-red-600 dark:text-red-400">
          Failed to load requirements. Please try again.
        </div>
      );
    }

    if (!requirements.length && !isLoading) {
      return (
        <div className="p-4 text-center text-gray-600 dark:text-gray-400">
          No requirements found matching your criteria.
        </div>
      );
    }

    const items = rowVirtualizer
      ? rowVirtualizer.getVirtualItems()
      : requirements.map((_, index) => ({ index }));

    return (
      <div
        className={cn(
          'grid gap-4',
          viewType === 'grid' && {
            'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4': true,
          },
          viewType === 'list' && 'grid-cols-1',
          className
        )}
        style={
          rowVirtualizer
            ? {
                height: `${rowVirtualizer.getTotalSize()}px`,
                position: 'relative',
              }
            : undefined
        }
      >
        {items.map((virtualRow) => {
          const requirement = requirements[virtualRow.index];
          if (!requirement) return null;

          return (
            <div
              key={requirement.id}
              className={cn(
                'transition-all duration-200',
                rowVirtualizer && {
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  transform: `translateY(${virtualRow.start}px)`,
                }
              )}
            >
              <RequirementCard
                requirement={requirement}
                onClick={() => handleRequirementClick(requirement.id)}
                className={cn(
                  'h-full',
                  viewType === 'list' && 'flex-row items-center'
                )}
                testId={`requirement-${requirement.id}`}
              />
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <ErrorBoundary
      fallback={
        <div className="p-4 text-center text-red-600 dark:text-red-400">
          An error occurred while displaying requirements.
        </div>
      }
    >
      <div
        ref={containerRef}
        className={cn(
          'relative overflow-auto',
          'min-h-[200px] max-h-[800px]',
          className
        )}
        role="region"
        aria-label="Transfer Requirements List"
      >
        {renderRequirements()}
        
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/50 dark:bg-black/50">
            <LoadingSpinner size="lg" />
          </div>
        )}
        
        <div ref={intersectionRef} className="h-4" />
      </div>
    </ErrorBoundary>
  );
});

RequirementList.displayName = 'RequirementList';

export default RequirementList;