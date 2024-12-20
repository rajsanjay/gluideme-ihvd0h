/**
 * @fileoverview Progress Tracker Component for visualizing student transfer requirement completion
 * Includes accessibility features, RTL support, and smooth animations
 * @version 1.0.0
 */

import React, { useMemo, useCallback } from 'react';
import { CircularProgress } from '@shadcn/ui'; // v0.1.0
import { Card } from '../common/card';
import type { TransferProgress, RequirementProgress } from '../../types/student';
import { useRequirements } from '../../hooks/useRequirements';
import { formatPercentage } from '../../lib/utils/format';

// Progress status color mapping with WCAG AA compliance
const STATUS_COLORS = {
  not_started: 'text-gray-500 dark:text-gray-400',
  in_progress: 'text-blue-600 dark:text-blue-400',
  completed: 'text-green-600 dark:text-green-400'
} as const;

interface ProgressTrackerProps {
  /** Progress data for the transfer requirements */
  progress: TransferProgress;
  /** Optional CSS classes */
  className?: string;
  /** Enable RTL support */
  isRTL?: boolean;
}

/**
 * Calculates the completion percentage with proper rounding
 * @param completed - Number of completed items
 * @param total - Total number of items
 * @returns Formatted percentage string
 */
const calculatePercentage = (completed: number, total: number): string => {
  if (total <= 0) return '0%';
  const percentage = (completed / total) * 100;
  return formatPercentage(Math.min(percentage, 100) / 100);
};

/**
 * Progress Tracker component for visualizing transfer requirement completion
 */
export const ProgressTracker: React.FC<ProgressTrackerProps> = ({
  progress,
  className = '',
  isRTL = false
}) => {
  const { operations } = useRequirements();

  // Memoize overall progress calculation
  const overallProgress = useMemo(() => {
    return calculatePercentage(progress.completedUnits, progress.requiredUnits);
  }, [progress.completedUnits, progress.requiredUnits]);

  // Handle requirement validation
  const handleValidateRequirement = useCallback(async (requirementId: string) => {
    try {
      await operations.validate(requirementId, []);
    } catch (error) {
      console.error('Validation failed:', error);
    }
  }, [operations]);

  /**
   * Renders the overall progress section
   */
  const renderOverallProgress = () => (
    <Card
      variant="elevated"
      padding="lg"
      className={`mb-6 ${isRTL ? 'rtl' : 'ltr'}`}
      role="region"
      aria-label="Overall Transfer Progress"
    >
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <h2 className="text-xl font-semibold">Overall Progress</h2>
          <p className="text-sm text-gray-600 dark:text-gray-300">
            {progress.completedUnits} of {progress.requiredUnits} units completed
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-300">
            Current GPA: {progress.currentGPA.toFixed(2)}
          </p>
        </div>
        <div className="relative" role="progressbar" aria-valuenow={parseInt(overallProgress)} aria-valuemin={0} aria-valuemax={100}>
          <CircularProgress
            value={parseInt(overallProgress)}
            size="xl"
            color={STATUS_COLORS[progress.overallStatus]}
            aria-label={`${overallProgress} complete`}
          />
          <span className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-lg font-semibold">
            {overallProgress}
          </span>
        </div>
      </div>
    </Card>
  );

  /**
   * Renders individual requirement progress items
   */
  const renderRequirementProgress = () => (
    <div
      className="space-y-4"
      role="list"
      aria-label="Requirement Progress"
    >
      {progress.requirementProgress.map((requirement: RequirementProgress) => (
        <Card
          key={requirement.requirementId}
          variant="outline"
          padding="md"
          className={`transition-all duration-200 hover:shadow-md ${isRTL ? 'rtl' : 'ltr'}`}
          role="listitem"
        >
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <h3 className="font-medium">
                Requirement {requirement.requirementId}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-300">
                {requirement.completedItems} of {requirement.totalItems} items completed
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <span className={`text-sm ${STATUS_COLORS[requirement.status]}`}>
                {requirement.status.replace('_', ' ')}
              </span>
              <button
                onClick={() => handleValidateRequirement(requirement.requirementId)}
                className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                aria-label={`Validate requirement ${requirement.requirementId}`}
              >
                Validate
              </button>
            </div>
          </div>
          <div className="mt-2 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className={`h-full rounded-full transition-all duration-500 ${STATUS_COLORS[requirement.status]}`}
              style={{
                width: calculatePercentage(requirement.completedItems, requirement.totalItems),
                transform: isRTL ? 'scaleX(-1)' : undefined
              }}
              role="progressbar"
              aria-valuenow={requirement.completedItems}
              aria-valuemin={0}
              aria-valuemax={requirement.totalItems}
            />
          </div>
        </Card>
      ))}
    </div>
  );

  return (
    <div
      className={`progress-tracker ${className}`}
      dir={isRTL ? 'rtl' : 'ltr'}
      role="region"
      aria-label="Transfer Progress Tracker"
    >
      {renderOverallProgress()}
      {renderRequirementProgress()}
    </div>
  );
};

// Display name for debugging
ProgressTracker.displayName = 'ProgressTracker';

export default ProgressTracker;