// @ts-check
import { z } from 'zod'; // v3.21.0 - Runtime type validation

/**
 * Valid HTTP methods for API requests
 */
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';

/**
 * Standardized error codes for API responses
 */
export type ErrorCode = 
  | 'BAD_REQUEST' 
  | 'UNAUTHORIZED' 
  | 'FORBIDDEN' 
  | 'NOT_FOUND' 
  | 'INTERNAL_SERVER_ERROR';

/**
 * Generic API response wrapper ensuring type safety
 * @template T The type of data contained in the response
 */
export interface ApiResponse<T> {
  /** The response payload */
  data: T;
  /** HTTP status code */
  status: number;
  /** Optional message providing additional context */
  message: string | null;
}

/**
 * Field-level validation error details
 */
export interface ValidationError {
  /** The field that failed validation */
  field: string;
  /** Human-readable error message */
  message: string;
  /** Machine-readable error code for programmatic handling */
  code: string;
}

/**
 * Comprehensive error response structure
 */
export interface ApiError {
  /** Standardized error code */
  code: ErrorCode;
  /** Human-readable error message */
  message: string;
  /** Array of field-level validation errors */
  errors: ValidationError[];
}

/**
 * Generic paginated response wrapper
 * @template T The type of items in the paginated response
 */
export interface PaginatedResponse<T> {
  /** Array of items for the current page */
  data: T[];
  /** Total number of items across all pages */
  total: number;
  /** Current page number (1-based) */
  page: number;
  /** Number of items per page */
  pageSize: number;
  /** Total number of pages available */
  totalPages: number;
}

/**
 * User data structure with comprehensive type information
 */
export interface User {
  /** Unique identifier for the user */
  id: string;
  /** User's email address */
  email: string;
  /** User's role (e.g., 'admin', 'student', 'counselor') */
  role: string;
  /** Optional institution ID for institution-specific users */
  institutionId: string | null;
  /** User preferences stored as key-value pairs */
  preferences: Record<string, unknown>;
  /** Timestamp of last login (ISO format) */
  lastLogin: string | null;
}

/**
 * Configuration object for API requests
 */
export interface ApiRequestConfig {
  /** HTTP method for the request */
  method: HttpMethod;
  /** Request URL (relative or absolute) */
  url: string;
  /** Request payload for POST/PUT/PATCH methods */
  data?: unknown;
  /** URL query parameters */
  params?: Record<string, string | number>;
  /** Custom request headers */
  headers?: Record<string, string>;
}

/**
 * Zod schema for runtime validation of API responses
 */
export const apiResponseSchema = z.object({
  data: z.unknown(),
  status: z.number().int().positive(),
  message: z.string().nullable()
});

/**
 * Zod schema for runtime validation of validation errors
 */
export const validationErrorSchema = z.object({
  field: z.string(),
  message: z.string(),
  code: z.string()
});

/**
 * Zod schema for runtime validation of API errors
 */
export const apiErrorSchema = z.object({
  code: z.enum(['BAD_REQUEST', 'UNAUTHORIZED', 'FORBIDDEN', 'NOT_FOUND', 'INTERNAL_SERVER_ERROR']),
  message: z.string(),
  errors: z.array(validationErrorSchema)
});

/**
 * Zod schema for runtime validation of paginated responses
 */
export const paginatedResponseSchema = z.object({
  data: z.array(z.unknown()),
  total: z.number().int().nonnegative(),
  page: z.number().int().positive(),
  pageSize: z.number().int().positive(),
  totalPages: z.number().int().nonnegative()
});

/**
 * Zod schema for runtime validation of user data
 */
export const userSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  role: z.string(),
  institutionId: z.string().nullable(),
  preferences: z.record(z.unknown()),
  lastLogin: z.string().nullable()
});