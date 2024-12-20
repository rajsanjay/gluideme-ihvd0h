/**
 * @fileoverview RequirementCard component for displaying transfer requirement information
 * Implements design system visual hierarchy and theme support with accessibility features
 * @version 1.0.0
 */

import * as React from 'react';
import { cn } from '@shadcn/ui'; // v0.1.0
import { Card } from '../common/card';
import { TransferRequirement } from '../../types/requirements';
import { formatDate } from '../../lib/utils/date';
import { ErrorBoundary } from '../common/error-boundary';
import { truncateText } from '../../lib/utils/format';

/**
 * Props interface for the RequirementCard component
 */
interface RequirementCardProps {
  /** Transfer requirement data to display */
  requirement: TransferRequirement;
  /** Click handler for card interaction */
  onClick?: (id: string) => void;
  /** Additional CSS classes */
  className?: string;
  /** Test ID for automated testing */
  testId?: string;
}

/**
 * Maps requirement status to theme-aware color classes
 */
const getStatusColor = (status: string): string => {
  const statusColors = {
    draft: 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-100',
    published: 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-100',
    archived: 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-100',
    deprecated: 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-100'
  };

  return statusColors[status] || statusColors.draft;
};

/**
 * Custom hook for managing card interactions and accessibility
 */
const useCardInteractions = (onClick?: (id: string) => void, id?: string) => {
  const handleClick = React.useCallback(() => {
    if (onClick && id) {
      onClick(id);
    }
  }, [onClick, id]);

  const handleKeyPress = React.useCallback((event: React.KeyboardEvent) => {
    if ((event.key === 'Enter' || event.key === ' ') && onClick && id) {
      event.preventDefault();
      onClick(id);
    }
  }, [onClick, id]);

  return {
    onClick: handleClick,
    onKeyPress: handleKeyPress,
    role: 'button',
    tabIndex: 0
  };
};

/**
 * RequirementCard component for displaying transfer requirement information
 * Implements 8-point grid system and WCAG 2.1 AA compliance
 */
export const RequirementCard = React.memo<RequirementCardProps>(({
  requirement,
  onClick,
  className,
  testId = 'requirement-card'
}) => {
  // Format dates and descriptions with error handling
  const formattedDate = React.useMemo(() => {
    try {
      return formatDate(requirement.effectiveDate, 'MMM d, yyyy');
    } catch (error) {
      console.error('Date formatting error:', error);
      return 'Invalid Date';
    }
  }, [requirement.effectiveDate]);

  const truncatedDescription = React.useMemo(() => {
    try {
      return truncateText(requirement.description, 150);
    } catch (error) {
      console.error('Text truncation error:', error);
      return requirement.description;
    }
  }, [requirement.description]);

  // Get interaction handlers and accessibility props
  const interactionProps = useCardInteractions(onClick, requirement.id);

  // Get status-specific styling
  const statusClass = React.useMemo(() => 
    getStatusColor(requirement.status),
    [requirement.status]
  );

  return (
    <ErrorBoundary
      fallback={
        <Card
          variant="outline"
          className="bg-red-50 dark:bg-red-900 p-4"
          role="alert"
        >
          <p>Error loading requirement card</p>
        </Card>
      }
    >
      <Card
        variant="default"
        padding="lg"
        interactive={!!onClick}
        className={cn(
          'relative overflow-hidden transition-all duration-200',
          'hover:shadow-md dark:hover:shadow-lg',
          'focus-visible:ring-2 focus-visible:ring-primary',
          'motion-reduce:transition-none',
          className
        )}
        data-testid={testId}
        {...interactionProps}
      >
        {/* Status Badge */}
        <div
          className={cn(
            'absolute top-4 right-4 px-2 py-1 rounded-full text-xs font-medium',
            statusClass
          )}
          aria-label={`Status: ${requirement.status}`}
        >
          {requirement.status}
        </div>

        {/* Title */}
        <h3 className="text-lg font-semibold mb-2 pr-24">
          {requirement.title}
        </h3>

        {/* Description */}
        <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
          {truncatedDescription}
        </p>

        {/* Metadata */}
        <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
          <span>
            Effective: {formattedDate}
          </span>
          <span className="flex items-center gap-2">
            <span className="sr-only">Major Code:</span>
            {requirement.majorCode}
          </span>
        </div>
      </Card>
    </ErrorBoundary>
  );
}, (prevProps, nextProps) => {
  // Custom memoization to prevent unnecessary rerenders
  return (
    prevProps.requirement.id === nextProps.requirement.id &&
    prevProps.requirement.status === nextProps.requirement.status &&
    prevProps.requirement.effectiveDate === nextProps.requirement.effectiveDate
  );
});

RequirementCard.displayName = 'RequirementCard';

export default RequirementCard;