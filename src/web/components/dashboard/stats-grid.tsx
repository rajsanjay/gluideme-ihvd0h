/**
 * @file Stats Grid Component
 * @version 1.0.0
 * @description A responsive grid component for displaying analytics metrics and statistics
 * in a dashboard layout. Implements the design system's grid layout with enhanced
 * accessibility and real-time update capabilities.
 */

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { cn } from 'class-variance-authority'; // v0.7.0
import AnalyticsCard from './analytics-card';
import type { AsyncState } from '../../types/common';

/**
 * Props interface for individual stat data
 */
interface StatData {
  /** Unique identifier for the stat */
  id: string;
  /** Display title for the stat */
  title: string;
  /** Current metric value */
  metric: number;
  /** Percentage change from previous period */
  change: number;
  /** Time series data for visualization */
  data: Array<{ x: string | number; y: number }>;
  /** Loading state for individual stat */
  loading?: boolean;
  /** Error state for individual stat */
  error?: Error | null;
}

/**
 * Props interface for the StatsGrid component
 */
export interface StatsGridProps {
  /** Array of statistics to display */
  stats: StatData[];
  /** Global loading state */
  loading?: boolean;
  /** Additional CSS classes */
  className?: string;
  /** Custom column configuration for different breakpoints */
  columnConfig?: {
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
  };
  /** Custom gap size in pixels */
  gap?: number;
  /** Interval for real-time updates in milliseconds */
  updateInterval?: number;
}

/**
 * Default column configuration for different breakpoints
 */
const DEFAULT_COLUMN_CONFIG = {
  sm: 1,
  md: 2,
  lg: 3,
  xl: 4,
};

/**
 * Generates responsive grid classes with enhanced customization
 */
const getGridClasses = (
  className?: string,
  columnConfig = DEFAULT_COLUMN_CONFIG,
  gap = 16
): string => {
  return cn(
    'w-full grid',
    `gap-${gap}`,
    `grid-cols-${columnConfig.sm}`,
    `md:grid-cols-${columnConfig.md}`,
    `lg:grid-cols-${columnConfig.lg}`,
    `xl:grid-cols-${columnConfig.xl}`,
    'auto-rows-fr',
    'p-4',
    className
  );
};

/**
 * Custom hook for handling grid resize events
 */
const useGridResize = () => {
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const gridRef = useRef<HTMLDivElement>(null);

  const updateDimensions = useCallback(() => {
    if (gridRef.current) {
      const { width, height } = gridRef.current.getBoundingClientRect();
      setDimensions({ width, height });
    }
  }, []);

  useEffect(() => {
    const observer = new ResizeObserver(updateDimensions);
    if (gridRef.current) {
      observer.observe(gridRef.current);
    }

    return () => observer.disconnect();
  }, [updateDimensions]);

  return { dimensions, gridRef };
};

/**
 * StatsGrid Component
 * 
 * A responsive grid component for displaying analytics metrics with real-time updates
 * and enhanced accessibility features.
 */
export const StatsGrid: React.FC<StatsGridProps> = ({
  stats,
  loading = false,
  className,
  columnConfig = DEFAULT_COLUMN_CONFIG,
  gap = 16,
  updateInterval = 30000,
}) => {
  const { dimensions, gridRef } = useGridResize();
  const updateTimer = useRef<NodeJS.Timeout>();

  // Handle real-time updates
  useEffect(() => {
    if (updateInterval > 0) {
      updateTimer.current = setInterval(() => {
        // Trigger data refresh logic here
      }, updateInterval);

      return () => {
        if (updateTimer.current) {
          clearInterval(updateTimer.current);
        }
      };
    }
  }, [updateInterval]);

  // Generate grid classes
  const gridClasses = useMemo(
    () => getGridClasses(className, columnConfig, gap),
    [className, columnConfig, gap]
  );

  return (
    <div
      ref={gridRef}
      className={gridClasses}
      role="grid"
      aria-busy={loading}
      aria-label="Analytics Dashboard"
    >
      {stats.map((stat) => (
        <div
          key={stat.id}
          role="gridcell"
          className="relative"
        >
          <AnalyticsCard
            title={stat.title}
            metric={stat.metric}
            change={stat.change}
            data={stat.data}
            loading={loading || stat.loading}
            error={stat.error}
            animate={dimensions.width > 0} // Enable animations after initial render
            className="h-full"
            ariaLabel={`${stat.title} analytics card`}
          />
        </div>
      ))}
    </div>
  );
};

// Set display name for dev tools
StatsGrid.displayName = 'StatsGrid';

export default StatsGrid;