"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query"; // ^4.29.0
import { DataTable } from "../common/data-table";
import { getRequirements } from "../../lib/api/requirements";
import type { PaginationParams, SortParams } from "../../types/common";
import type { TransferRequirement } from "../../types/requirements";

/**
 * Interface for activity item displayed in the table
 */
interface ActivityItem {
  id: string;
  institution: string;
  major: string;
  status: string;
  updatedAt: string;
  type: string;
  version: number;
}

/**
 * Props interface for the RecentActivity component
 */
interface RecentActivityProps {
  limit?: number;
  className?: string;
}

/**
 * Transforms a TransferRequirement into an ActivityItem
 */
const transformRequirementToActivity = (
  requirement: TransferRequirement
): ActivityItem => ({
  id: requirement.id,
  institution: requirement.sourceInstitutionId,
  major: requirement.majorCode,
  status: requirement.status,
  updatedAt: requirement.updatedAt,
  type: requirement.type,
  version: requirement.version.versionNumber,
});

/**
 * Custom hook for managing recent activity data with React Query
 */
const useRecentActivity = (
  limit: number,
  paginationParams: PaginationParams,
  sortParams?: SortParams
) => {
  // Query key that includes all parameters that affect the data
  const queryKey = React.useMemo(
    () => ["recentActivity", paginationParams, sortParams, limit],
    [paginationParams, sortParams, limit]
  );

  // Configure query with React Query
  return useQuery(
    queryKey,
    async () => {
      const response = await getRequirements({
        page: paginationParams.page,
        limit: paginationParams.pageSize,
        sort: sortParams?.sortBy
          ? `${sortParams.sortBy}:${sortParams.direction}`
          : undefined,
      });
      return {
        data: response.data.data.map(transformRequirementToActivity),
        total: response.data.total,
      };
    },
    {
      keepPreviousData: true,
      staleTime: 30000, // Consider data stale after 30 seconds
      cacheTime: 300000, // Cache data for 5 minutes
      refetchOnWindowFocus: true,
      retry: 2,
    }
  );
};

/**
 * Status badge renderer with proper ARIA labels
 */
const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const statusStyles = {
    draft: "bg-yellow-100 text-yellow-800",
    published: "bg-green-100 text-green-800",
    archived: "bg-gray-100 text-gray-800",
    deprecated: "bg-red-100 text-red-800",
  };

  return (
    <span
      className={`px-2 py-1 rounded-full text-xs font-medium ${
        statusStyles[status as keyof typeof statusStyles]
      }`}
      role="status"
      aria-label={`Status: ${status}`}
    >
      {status}
    </span>
  );
};

/**
 * RecentActivity Component
 * 
 * Displays a table of recent transfer requirement updates with sorting,
 * pagination, and optimized performance through React Query integration.
 */
export const RecentActivity: React.FC<RecentActivityProps> = ({
  limit = 10,
  className,
}) => {
  // State management for sorting and pagination
  const [sortParams, setSortParams] = React.useState<SortParams>();
  const [paginationParams, setPaginationParams] = React.useState<PaginationParams>({
    page: 1,
    pageSize: limit,
  });

  // Fetch data using React Query
  const { data, isLoading, error, isError } = useRecentActivity(
    limit,
    paginationParams,
    sortParams
  );

  // Memoized table columns configuration
  const columns = React.useMemo(
    () => [
      {
        id: "institution",
        header: "Institution",
        accessorKey: "institution",
        cell: (info: any) => info.getValue(),
      },
      {
        id: "major",
        header: "Major",
        accessorKey: "major",
        cell: (info: any) => info.getValue(),
      },
      {
        id: "type",
        header: "Type",
        accessorKey: "type",
        cell: (info: any) => info.getValue(),
      },
      {
        id: "status",
        header: "Status",
        accessorKey: "status",
        cell: (info: any) => <StatusBadge status={info.getValue()} />,
      },
      {
        id: "version",
        header: "Version",
        accessorKey: "version",
        cell: (info: any) => `v${info.getValue()}`,
      },
      {
        id: "updatedAt",
        header: "Last Updated",
        accessorKey: "updatedAt",
        cell: (info: any) => new Date(info.getValue()).toLocaleDateString(),
      },
    ],
    []
  );

  // Handlers for pagination and sorting
  const handlePageChange = React.useCallback(
    (params: PaginationParams) => {
      setPaginationParams(params);
    },
    []
  );

  const handleSort = React.useCallback((params: SortParams) => {
    setSortParams(params);
  }, []);

  return (
    <div className={className}>
      <h2 className="text-lg font-semibold mb-4">Recent Updates</h2>
      <DataTable
        data={data?.data ?? []}
        columns={columns}
        totalItems={data?.total ?? 0}
        onPageChange={handlePageChange}
        onSort={handleSort}
        loading={isLoading}
        error={isError ? (error as Error).message : null}
        className="bg-white rounded-lg shadow"
        virtualScrolling={false}
        customRenderers={{
          status: (value) => <StatusBadge status={value} />,
        }}
        initialPage={paginationParams.page}
        initialPageSize={paginationParams.pageSize}
      />
    </div>
  );
};

export default RecentActivity;