"use client";

import React, { useCallback, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ErrorBoundary } from '../../components/common/error-boundary';
import { StatsGrid } from '../../components/dashboard/stats-grid';
import { RecentActivity } from '../../components/dashboard/recent-activity';
import { useAuth } from '../../hooks/useAuth';
import { getRequirements } from '../../lib/api/requirements';
import { formatPercentage } from '../../lib/utils/format';

/**
 * Interface for dashboard analytics metrics
 */
interface DashboardMetrics {
  activeRules: number;
  pendingReviews: number;
  totalInstitutions: number;
  completedTransfers: number;
  lastUpdated: Date;
}

/**
 * Custom hook for fetching and managing dashboard metrics
 */
const useDashboardMetrics = (refetchInterval: number | false = 30000) => {
  return useQuery<DashboardMetrics>(
    ['dashboardMetrics'],
    async () => {
      const response = await getRequirements({
        page: 1,
        limit: 1,
        filters: {
          status: 'published'
        }
      });

      // Transform API response to metrics format
      return {
        activeRules: response.data.total,
        pendingReviews: response.data.data.filter(r => r.status === 'draft').length,
        totalInstitutions: new Set(response.data.data.map(r => r.sourceInstitutionId)).size,
        completedTransfers: response.data.data.filter(r => r.status === 'published').length,
        lastUpdated: new Date()
      };
    },
    {
      refetchInterval,
      staleTime: 60000, // Consider data stale after 1 minute
      cacheTime: 300000, // Cache for 5 minutes
      retry: 2,
      onError: (error) => {
        console.error('Failed to fetch dashboard metrics:', error);
      }
    }
  );
};

/**
 * Error fallback component for the dashboard
 */
const DashboardErrorFallback: React.FC<{ error: Error }> = ({ error }) => (
  <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
    <h3 className="text-lg font-semibold text-red-800 mb-2">
      Dashboard Error
    </h3>
    <p className="text-red-600">
      {error.message || 'An error occurred while loading the dashboard'}
    </p>
  </div>
);

/**
 * Main dashboard page component implementing the administrator dashboard layout
 * with role-based content visibility and real-time updates
 */
const DashboardPage: React.FC = () => {
  const { state: authState, checkPermission } = useAuth();
  const { data: metrics, isLoading, error } = useDashboardMetrics();

  // Check user permissions for dashboard access
  const canViewMetrics = checkPermission('view_dashboard_metrics');
  const canViewActivity = checkPermission('view_recent_activity');

  // Transform metrics for StatsGrid component
  const statsData = React.useMemo(() => {
    if (!metrics) return [];

    return [
      {
        id: 'active-rules',
        title: 'Active Rules',
        metric: metrics.activeRules,
        change: 0.05, // Example change percentage
        data: [], // Time series data would be added here
      },
      {
        id: 'pending-reviews',
        title: 'Pending Reviews',
        metric: metrics.pendingReviews,
        change: -0.02, // Example change percentage
        data: [],
      },
      {
        id: 'institutions',
        title: 'Total Institutions',
        metric: metrics.totalInstitutions,
        change: 0.03, // Example change percentage
        data: [],
      },
      {
        id: 'completed-transfers',
        title: 'Completed Transfers',
        metric: metrics.completedTransfers,
        change: 0.08, // Example change percentage
        data: [],
      },
    ];
  }, [metrics]);

  // Handle real-time updates setup
  useEffect(() => {
    const ws = new WebSocket(process.env.NEXT_PUBLIC_WS_URL || '');
    
    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);
      // Handle real-time updates here
    };

    return () => {
      ws.close();
    };
  }, []);

  if (!authState.isAuthenticated) {
    return (
      <div className="p-6">
        <p className="text-red-600">
          Please log in to access the dashboard
        </p>
      </div>
    );
  }

  return (
    <ErrorBoundary fallback={<DashboardErrorFallback error={error as Error} />}>
      <div className="p-6 space-y-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
            Dashboard
          </h1>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            Last updated: {metrics?.lastUpdated.toLocaleString()}
          </span>
        </div>

        {canViewMetrics && (
          <StatsGrid
            stats={statsData}
            loading={isLoading}
            className="mb-8"
            columnConfig={{ sm: 1, md: 2, lg: 4 }}
            updateInterval={30000}
          />
        )}

        {canViewActivity && (
          <RecentActivity
            limit={10}
            className="mt-8"
          />
        )}
      </div>
    </ErrorBoundary>
  );
};

// Set display name for dev tools
DashboardPage.displayName = 'DashboardPage';

export default DashboardPage;