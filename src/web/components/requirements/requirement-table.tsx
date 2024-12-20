"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query"; // v4.29.0
import { createColumnHelper } from "@tanstack/react-table"; // v8.9.3
import { useDebounce } from "use-debounce"; // v9.0.0
import DataTable from "../common/data-table";
import type { TransferRequirement, RequirementStatus } from "../../types/requirements";
import type { PaginationParams, SortParams, DateRange } from "../../types/common";

/**
 * Props interface for the RequirementTable component
 */
interface RequirementTableProps {
  onRowClick?: (requirement: TransferRequirement) => void;
  filters?: RequirementFilters;
  className?: string;
  initialSort?: SortParams;
  pageSize?: number;
  onError?: (error: Error) => void;
  enableSelection?: boolean;
  onSelectionChange?: (selected: TransferRequirement[]) => void;
}

/**
 * Interface for requirement filtering options
 */
interface RequirementFilters {
  status?: RequirementStatus[];
  searchTerm?: string;
  institutionId?: string;
  dateRange?: DateRange;
  majorCodes?: string[];
  tags?: string[];
}

/**
 * Custom hook for generating table column definitions
 */
const useRequirementColumns = (
  onEdit?: (requirement: TransferRequirement) => void,
  onDelete?: (requirement: TransferRequirement) => void
) => {
  const columnHelper = createColumnHelper<TransferRequirement>();

  return React.useMemo(
    () => [
      columnHelper.accessor("title", {
        header: "Title",
        cell: (info) => (
          <span className="font-medium text-neutral-900">{info.getValue()}</span>
        ),
        sortingFn: "alphanumeric",
      }),
      columnHelper.accessor("status", {
        header: "Status",
        cell: (info) => (
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
              ${getStatusColor(info.getValue())}`}
            role="status"
          >
            {info.getValue()}
          </span>
        ),
      }),
      columnHelper.accessor("effectiveDate", {
        header: "Effective Date",
        cell: (info) => formatDate(info.getValue()),
        sortingFn: "datetime",
      }),
      columnHelper.accessor("institution", {
        header: "Institution",
        cell: (info) => info.getValue()?.name || "N/A",
      }),
      columnHelper.display({
        id: "actions",
        header: "Actions",
        cell: (info) => (
          <div className="flex items-center gap-2">
            {onEdit && (
              <button
                onClick={() => onEdit(info.row.original)}
                className="text-primary-600 hover:text-primary-700"
                aria-label={`Edit ${info.row.original.title}`}
              >
                Edit
              </button>
            )}
            {onDelete && (
              <button
                onClick={() => onDelete(info.row.original)}
                className="text-red-600 hover:text-red-700"
                aria-label={`Delete ${info.row.original.title}`}
              >
                Delete
              </button>
            )}
          </div>
        ),
      }),
    ],
    [columnHelper, onEdit, onDelete]
  );
};

/**
 * Helper function to get status badge color
 */
const getStatusColor = (status: RequirementStatus): string => {
  const colors = {
    draft: "bg-yellow-100 text-yellow-800",
    published: "bg-green-100 text-green-800",
    archived: "bg-neutral-100 text-neutral-800",
    deprecated: "bg-red-100 text-red-800",
  };
  return colors[status] || colors.draft;
};

/**
 * Helper function to format dates
 */
const formatDate = (date: string): string => {
  return new Date(date).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
};

/**
 * RequirementTable Component
 * 
 * A comprehensive table component for displaying and managing transfer requirements
 * with advanced features like sorting, filtering, and accessibility support.
 */
export const RequirementTable: React.FC<RequirementTableProps> = ({
  onRowClick,
  filters,
  className,
  initialSort,
  pageSize = 10,
  onError,
  enableSelection = false,
  onSelectionChange,
}) => {
  // State management
  const [currentPage, setCurrentPage] = React.useState(1);
  const [debouncedFilters] = useDebounce(filters, 300);

  // Fetch requirements data
  const {
    data,
    isLoading,
    error,
    refetch,
  } = useQuery(
    ["requirements", currentPage, pageSize, debouncedFilters, initialSort],
    async () => {
      try {
        const response = await fetch("/api/requirements", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            page: currentPage,
            pageSize,
            filters: debouncedFilters,
            sort: initialSort,
          }),
        });

        if (!response.ok) {
          throw new Error("Failed to fetch requirements");
        }

        return await response.json();
      } catch (err) {
        onError?.(err as Error);
        throw err;
      }
    },
    {
      keepPreviousData: true,
      staleTime: 30000, // 30 seconds
    }
  );

  // Generate columns
  const columns = useRequirementColumns();

  // Handle page changes
  const handlePageChange = (params: PaginationParams) => {
    setCurrentPage(params.page);
  };

  // Handle sort changes
  const handleSort = (sortParams: SortParams) => {
    refetch();
  };

  // Handle selection changes
  const handleSelectionChange = (selected: TransferRequirement[]) => {
    onSelectionChange?.(selected);
  };

  // Error handling effect
  React.useEffect(() => {
    if (error) {
      onError?.(error as Error);
    }
  }, [error, onError]);

  return (
    <DataTable<TransferRequirement>
      data={data?.items || []}
      columns={columns}
      totalItems={data?.total || 0}
      onPageChange={handlePageChange}
      onSort={handleSort}
      loading={isLoading}
      error={error?.message}
      className={className}
      virtualScrolling={true}
      rowSelection={enableSelection}
      onRowSelect={handleSelectionChange}
      initialPage={currentPage}
      initialPageSize={pageSize}
      customRenderers={{
        status: (value: RequirementStatus) => (
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
              ${getStatusColor(value)}`}
            role="status"
          >
            {value}
          </span>
        ),
        effectiveDate: (value: string) => formatDate(value),
      }}
    />
  );
};

export default RequirementTable;