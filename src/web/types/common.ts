// @ts-check
import { z } from 'zod'; // v3.21.0 - Runtime type validation
import type { ApiResponse } from './api';

/**
 * Possible states for async operations
 */
export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

/**
 * Sort direction options for data ordering
 */
export type SortDirection = 'asc' | 'desc';

/**
 * Available view modes for data presentation
 */
export type ViewMode = 'list' | 'grid' | 'table';

/**
 * Base interface for entities requiring unique identification
 */
export interface Identifiable {
  /** Unique identifier for the entity */
  id: string;
}

/**
 * Common timestamp fields for entity auditing
 */
export interface Timestamps {
  /** ISO timestamp of entity creation */
  createdAt: string;
  /** ISO timestamp of last entity modification */
  updatedAt: string;
}

/**
 * Standard pagination parameters for list views
 */
export interface PaginationParams {
  /** Current page number (1-based) */
  page: number;
  /** Number of items per page */
  pageSize: number;
}

/**
 * Common sorting parameters for data ordering
 */
export interface SortParams {
  /** Field name to sort by */
  sortBy: string;
  /** Sort direction (ascending or descending) */
  direction: SortDirection;
}

/**
 * Flexible filtering parameters for data querying
 */
export interface FilterParams {
  /** Key-value pairs of filter criteria */
  filters: Record<string, string | number | boolean | null>;
}

/**
 * Generic async operation state tracking
 * @template T The type of data being loaded
 */
export interface AsyncState<T> {
  /** Current loading state */
  status: LoadingState;
  /** Error message if operation failed */
  error: string | null;
  /** Operation result data */
  data: T | null;
}

/**
 * Standardized select/dropdown option structure
 */
export interface SelectOption {
  /** Option value */
  value: string | number;
  /** Display label */
  label: string;
  /** Whether the option is disabled */
  disabled: boolean;
}

/**
 * Date range selection structure
 */
export interface DateRange {
  /** Start date in ISO format */
  startDate: string;
  /** End date in ISO format */
  endDate: string;
}

/**
 * Runtime validation schemas for common types
 */
export const schemas = {
  pagination: z.object({
    page: z.number().int().positive(),
    pageSize: z.number().int().positive()
  }),

  sort: z.object({
    sortBy: z.string(),
    direction: z.enum(['asc', 'desc'])
  }),

  filter: z.object({
    filters: z.record(z.union([
      z.string(),
      z.number(),
      z.boolean(),
      z.null()
    ]))
  }),

  selectOption: z.object({
    value: z.union([z.string(), z.number()]),
    label: z.string(),
    disabled: z.boolean()
  }),

  dateRange: z.object({
    startDate: z.string().datetime(),
    endDate: z.string().datetime()
  })
};

/**
 * Type guard to check if a value is a valid LoadingState
 */
export const isLoadingState = (value: unknown): value is LoadingState => {
  return ['idle', 'loading', 'success', 'error'].includes(value as string);
};

/**
 * Type guard to check if a value is a valid SortDirection
 */
export const isSortDirection = (value: unknown): value is SortDirection => {
  return ['asc', 'desc'].includes(value as string);
};

/**
 * Type guard to check if a value is a valid ViewMode
 */
export const isViewMode = (value: unknown): value is ViewMode => {
  return ['list', 'grid', 'table'].includes(value as string);
};