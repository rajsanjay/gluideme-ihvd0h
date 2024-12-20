"use client";

import * as React from "react";
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  ColumnDef,
  SortingState,
  flexRender,
  Row,
} from "@tanstack/react-table"; // v8.9.3
import { useVirtualizer } from "@tanstack/react-virtual"; // v3.0.0
import { cn } from "class-variance-authority"; // v0.7.0
import Pagination from "./pagination";
import { usePagination } from "../../hooks/usePagination";
import type { PaginationParams, SortParams } from "../../types/common";

// Style variants for the data table
const tableVariants = {
  base: "w-full overflow-hidden border border-neutral-200 rounded-lg shadow-sm",
  header: "bg-neutral-50 px-6 py-3 text-left text-sm font-medium text-neutral-700",
  cell: "px-6 py-4 whitespace-nowrap text-sm text-neutral-900",
  sortable: "cursor-pointer hover:bg-neutral-100 focus:outline-none focus:ring-2 focus:ring-primary-500",
  loading: "opacity-50 pointer-events-none",
  error: "border-red-300 bg-red-50",
  selected: "bg-primary-50",
  virtualRow: "absolute top-0 left-0 w-full",
};

// Props interface for the DataTable component
export interface DataTableProps<T> {
  data: T[];
  columns: ColumnDef<T>[];
  totalItems: number;
  onPageChange: (params: PaginationParams) => void;
  onSort?: (sortParams: SortParams) => void;
  loading?: boolean;
  error?: string | null;
  className?: string;
  virtualScrolling?: boolean;
  rowSelection?: boolean;
  onRowSelect?: (selectedRows: T[]) => void;
  customRenderers?: Record<string, (value: any) => React.ReactNode>;
  initialPage?: number;
  initialPageSize?: number;
}

/**
 * DataTable Component
 * 
 * A comprehensive data table component with sorting, pagination, virtualization,
 * and accessibility features. Implements WCAG 2.1 AA standards.
 */
export function DataTable<T>({
  data,
  columns,
  totalItems,
  onPageChange,
  onSort,
  loading = false,
  error = null,
  className,
  virtualScrolling = false,
  rowSelection = false,
  onRowSelect,
  customRenderers,
  initialPage = 1,
  initialPageSize = 10,
}: DataTableProps<T>) {
  // Table ref for virtualization
  const tableRef = React.useRef<HTMLDivElement>(null);

  // State management
  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [selectedRows, setSelectedRows] = React.useState<Record<string, boolean>>({});

  // Initialize pagination hook
  const {
    paginationParams,
    totalPages,
    handlePageChange,
    handlePageSizeChange,
    isLoading: paginationLoading,
  } = usePagination({
    initialPage,
    initialPageSize,
    totalItems,
    onPageChange,
  });

  // Initialize table instance
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    state: {
      sorting,
    },
    onSortingChange: (updatedSort) => {
      setSorting(updatedSort as SortingState);
      if (onSort && updatedSort.length > 0) {
        const [sort] = updatedSort;
        onSort({
          sortBy: sort.id,
          direction: sort.desc ? "desc" : "asc",
        });
      }
    },
    enableSorting: true,
  });

  // Set up virtualization if enabled
  const { rows } = table.getRowModel();
  const rowVirtualizer = virtualScrolling
    ? useVirtualizer({
        count: rows.length,
        getScrollElement: () => tableRef.current,
        estimateSize: () => 53, // Approximate row height
        overscan: 10,
      })
    : null;

  // Handle row selection
  const handleRowSelect = React.useCallback(
    (row: Row<T>) => {
      if (!rowSelection) return;

      const newSelectedRows = {
        ...selectedRows,
        [row.id]: !selectedRows[row.id],
      };
      setSelectedRows(newSelectedRows);

      if (onRowSelect) {
        const selectedData = rows
          .filter((r) => newSelectedRows[r.id])
          .map((r) => r.original);
        onRowSelect(selectedData);
      }
    },
    [rowSelection, selectedRows, rows, onRowSelect]
  );

  // Render table header
  const renderHeader = () => (
    <thead className="bg-neutral-50">
      {table.getHeaderGroups().map((headerGroup) => (
        <tr key={headerGroup.id}>
          {rowSelection && (
            <th className={tableVariants.header}>
              <input
                type="checkbox"
                onChange={() => {
                  const allSelected = Object.keys(selectedRows).length === rows.length;
                  const newSelectedRows = allSelected
                    ? {}
                    : rows.reduce((acc, row) => ({ ...acc, [row.id]: true }), {});
                  setSelectedRows(newSelectedRows);
                }}
                checked={Object.keys(selectedRows).length === rows.length}
                aria-label="Select all rows"
              />
            </th>
          )}
          {headerGroup.headers.map((header) => (
            <th
              key={header.id}
              className={cn(tableVariants.header, header.column.getCanSort() && tableVariants.sortable)}
              onClick={header.column.getToggleSortingHandler()}
              role={header.column.getCanSort() ? "button" : undefined}
              aria-sort={header.column.getIsSorted() ? (header.column.getIsSorted() === "desc" ? "descending" : "ascending") : undefined}
            >
              {flexRender(header.column.columnDef.header, header.getContext())}
              {header.column.getIsSorted() && (
                <span className="ml-2" aria-hidden="true">
                  {header.column.getIsSorted() === "desc" ? "↓" : "↑"}
                </span>
              )}
            </th>
          ))}
        </tr>
      ))}
    </thead>
  );

  // Render table body
  const renderBody = () => (
    <tbody>
      {virtualScrolling && rowVirtualizer ? (
        <tr style={{ height: `${rowVirtualizer.getTotalSize()}px` }}>
          <td colSpan={columns.length + (rowSelection ? 1 : 0)}>
            {rowVirtualizer.getVirtualItems().map((virtualRow) => {
              const row = rows[virtualRow.index];
              return (
                <tr
                  key={row.id}
                  className={cn(
                    tableVariants.virtualRow,
                    selectedRows[row.id] && tableVariants.selected
                  )}
                  style={{
                    height: `${virtualRow.size}px`,
                    transform: `translateY(${virtualRow.start}px)`,
                  }}
                  onClick={() => handleRowSelect(row)}
                >
                  {rowSelection && (
                    <td className={tableVariants.cell}>
                      <input
                        type="checkbox"
                        checked={!!selectedRows[row.id]}
                        onChange={() => handleRowSelect(row)}
                        aria-label={`Select row ${virtualRow.index + 1}`}
                      />
                    </td>
                  )}
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className={tableVariants.cell}>
                      {customRenderers?.[cell.column.id]
                        ? customRenderers[cell.column.id](cell.getValue())
                        : flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              );
            })}
          </td>
        </tr>
      ) : (
        rows.map((row) => (
          <tr
            key={row.id}
            className={cn(selectedRows[row.id] && tableVariants.selected)}
            onClick={() => handleRowSelect(row)}
          >
            {rowSelection && (
              <td className={tableVariants.cell}>
                <input
                  type="checkbox"
                  checked={!!selectedRows[row.id]}
                  onChange={() => handleRowSelect(row)}
                  aria-label={`Select row ${row.id}`}
                />
              </td>
            )}
            {row.getVisibleCells().map((cell) => (
              <td key={cell.id} className={tableVariants.cell}>
                {customRenderers?.[cell.column.id]
                  ? customRenderers[cell.column.id](cell.getValue())
                  : flexRender(cell.column.columnDef.cell, cell.getContext())}
              </td>
            ))}
          </tr>
        ))
      )}
    </tbody>
  );

  return (
    <div className="space-y-4">
      <div
        ref={tableRef}
        className={cn(
          tableVariants.base,
          loading && tableVariants.loading,
          error && tableVariants.error,
          className
        )}
        style={{ maxHeight: virtualScrolling ? "400px" : undefined }}
        role="region"
        aria-label="Data table"
        aria-busy={loading}
      >
        <table className="min-w-full divide-y divide-neutral-200">
          {renderHeader()}
          {renderBody()}
        </table>
      </div>

      {error && (
        <div className="text-red-600 text-sm p-2" role="alert">
          {error}
        </div>
      )}

      <Pagination
        currentPage={paginationParams.page}
        pageSize={paginationParams.pageSize}
        totalItems={totalItems}
        onPageChange={handlePageChange}
        onPageSizeChange={handlePageSizeChange}
        showPageSizeSelector
        responsive
      />
    </div>
  );
}

export default DataTable;