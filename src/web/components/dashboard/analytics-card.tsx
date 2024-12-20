/**
 * @file Analytics Card Component
 * @version 1.0.0
 * @description A reusable analytics card component for displaying metric data with charts
 * in the dashboard. Supports various chart types, loading states, responsive design,
 * theme modes, and comprehensive accessibility features.
 */

import React, { useCallback, useEffect, useMemo } from 'react';
import { useTheme } from 'next-themes'; // v0.2.1
import { cn } from 'class-variance-authority'; // v0.7.0
import Card from '../common/card';
import LoadingSpinner from '../common/loading-spinner';
import ErrorBoundary from '../common/error-boundary';
import Chart from './chart';
import { formatPercentage } from '../../lib/utils/format';

/**
 * Props interface for the AnalyticsCard component
 */
export interface AnalyticsCardProps {
  /** Card title with optional i18n support */
  title: string;
  /** Primary metric value with formatting options */
  metric: number;
  /** Percentage change from previous period */
  change: number;
  /** Time series data for chart with validation */
  data: Array<{ x: string | number; y: number }>;
  /** Type of chart to display */
  chartType?: 'line' | 'bar' | 'area';
  /** Loading state indicator */
  loading?: boolean;
  /** Error state with custom handling */
  error?: Error | null;
  /** Error retry callback */
  onRetry?: () => void;
  /** Theme override */
  theme?: 'light' | 'dark' | 'system';
  /** Animation control flag */
  animate?: boolean;
  /** Additional CSS classes */
  className?: string;
  /** Accessibility label */
  ariaLabel?: string;
}

/**
 * Custom hook for managing card animations
 */
const useCardAnimation = (enabled: boolean = true) => {
  const prefersReducedMotion = useMemo(
    () => window?.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches,
    []
  );

  return {
    enabled: enabled && !prefersReducedMotion,
    classes: enabled && !prefersReducedMotion
      ? 'transition-all duration-300 ease-in-out'
      : '',
  };
};

/**
 * Custom hook for metric value formatting
 */
const useMetricFormatter = (value: number, locale?: string) => {
  return useMemo(() => {
    try {
      return new Intl.NumberFormat(locale || navigator.language, {
        maximumFractionDigits: 2,
        minimumFractionDigits: 0,
      }).format(value);
    } catch (error) {
      console.error('Error formatting metric:', error);
      return value.toString();
    }
  }, [value, locale]);
};

/**
 * AnalyticsCard Component
 * 
 * A comprehensive analytics card component for displaying metric data with charts.
 * Supports various chart types, loading states, and theme modes.
 */
const AnalyticsCard: React.FC<AnalyticsCardProps> = ({
  title,
  metric,
  change,
  data,
  chartType = 'line',
  loading = false,
  error = null,
  onRetry,
  theme: themeOverride,
  animate = true,
  className,
  ariaLabel,
}) => {
  const { theme, systemTheme } = useTheme();
  const animation = useCardAnimation(animate);
  const formattedMetric = useMetricFormatter(metric);
  const formattedChange = formatPercentage(Math.abs(change));

  // Determine current theme mode
  const currentTheme = themeOverride || theme || systemTheme || 'light';

  // Memoize card classes
  const cardClasses = useMemo(() => {
    return cn(
      'relative overflow-hidden rounded-lg',
      animation.classes,
      loading && 'opacity-60 pointer-events-none',
      error && 'border-red-500',
      className
    );
  }, [animation.classes, loading, error, className]);

  // Handle chart data updates
  useEffect(() => {
    if (data && !loading && !error) {
      // Trigger any necessary data transformations or updates
    }
  }, [data, loading, error]);

  // Handle retry action
  const handleRetry = useCallback(() => {
    if (onRetry) {
      onRetry();
    }
  }, [onRetry]);

  // Render error state
  if (error) {
    return (
      <Card
        variant="outline"
        padding="lg"
        className={cardClasses}
        aria-label={`${title} - Error`}
      >
        <div className="flex flex-col items-center justify-center p-6 text-center">
          <p className="text-red-600 dark:text-red-400 mb-4">
            Failed to load analytics data
          </p>
          {onRetry && (
            <button
              onClick={handleRetry}
              className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              Retry
            </button>
          )}
        </div>
      </Card>
    );
  }

  return (
    <ErrorBoundary
      fallback={
        <div className="text-red-600 dark:text-red-400 p-4">
          An error occurred while rendering the analytics card
        </div>
      }
    >
      <Card
        variant="outline"
        padding="lg"
        className={cardClasses}
        aria-label={ariaLabel || title}
      >
        <div className="space-y-4">
          {/* Header */}
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
              {title}
            </h3>
            {loading && <LoadingSpinner size="sm" />}
          </div>

          {/* Metric Display */}
          <div className="flex items-baseline space-x-4">
            <span className="text-3xl font-semibold text-gray-900 dark:text-gray-100">
              {formattedMetric}
            </span>
            <span
              className={cn(
                'inline-flex items-baseline px-2.5 py-0.5 rounded-full text-sm font-medium',
                change >= 0
                  ? 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100'
                  : 'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-100'
              )}
            >
              <span className="sr-only">
                {change >= 0 ? 'Increased by' : 'Decreased by'}
              </span>
              {change >= 0 ? '↑' : '↓'} {formattedChange}
            </span>
          </div>

          {/* Chart */}
          <div className="h-64">
            <Chart
              chartType={chartType}
              data={{
                status: loading ? 'loading' : 'success',
                error: null,
                data: data,
              }}
              title={title}
              xAxisKey="x"
              dataKeys={['y']}
              height={256}
              className="mt-4"
              ariaLabel={`${title} chart`}
            />
          </div>
        </div>
      </Card>
    </ErrorBoundary>
  );
};

// Set display name for dev tools
AnalyticsCard.displayName = 'AnalyticsCard';

export default AnalyticsCard;