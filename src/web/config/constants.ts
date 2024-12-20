/**
 * @fileoverview Global constants and configuration values for the frontend application
 * @version 1.0.0
 * 
 * This file contains centralized configuration constants used throughout the application,
 * including API settings, validation rules, pagination defaults, and caching configurations.
 * All values are aligned with system requirements for performance, security, and scalability.
 */

/**
 * API configuration constants for axios client
 * Includes base URL, timeout settings, and retry policies
 */
export const API_CONFIG = {
  /** Base API URL with fallback to localhost for development */
  BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  /** Request timeout in milliseconds (5 seconds) */
  TIMEOUT: 5000,
  /** Number of retry attempts for failed requests */
  RETRY_ATTEMPTS: 3,
  /** Delay between retry attempts in milliseconds */
  RETRY_DELAY: 1000,
} as const;

/**
 * Pagination configuration constants
 * Defines limits and defaults for paginated data retrieval
 */
export const PAGINATION = {
  /** Default number of items per page */
  DEFAULT_PAGE_SIZE: 10,
  /** Maximum allowed items per page */
  MAX_PAGE_SIZE: 100,
  /** Minimum allowed items per page */
  MIN_PAGE_SIZE: 5,
} as const;

/**
 * Cache configuration constants
 * Defines caching strategies and timeouts
 */
export const CACHE = {
  /** Default cache TTL in seconds (1 hour) */
  TTL: 3600,
  /** Maximum cache age in seconds (24 hours) */
  MAX_AGE: 86400,
  /** Stale-while-revalidate window in seconds (5 minutes) */
  STALE_WHILE_REVALIDATE: 300,
} as const;

/**
 * Validation rule constants
 * Defines security and data integrity constraints
 */
export const VALIDATION = {
  /** Minimum password length requirement */
  MIN_PASSWORD_LENGTH: 8,
  /** Maximum file size in bytes (5MB) */
  MAX_FILE_SIZE: 5242880,
  /** Allowed file types for document uploads */
  ALLOWED_FILE_TYPES: ['.pdf', '.doc', '.docx', '.txt'] as const,
} as const;

/**
 * HTTP status codes
 * Comprehensive set of status codes for consistent error handling
 */
export enum HTTP_STATUS {
  /** Successful response */
  OK = 200,
  /** Invalid request parameters */
  BAD_REQUEST = 400,
  /** Authentication required */
  UNAUTHORIZED = 401,
  /** Insufficient permissions */
  FORBIDDEN = 403,
  /** Resource not found */
  NOT_FOUND = 404,
  /** Internal server error */
  SERVER_ERROR = 500,
  /** Service temporarily unavailable */
  SERVICE_UNAVAILABLE = 503,
}

/**
 * Type definitions for configuration objects to ensure type safety
 */
export type ApiConfig = typeof API_CONFIG;
export type PaginationConfig = typeof PAGINATION;
export type CacheConfig = typeof CACHE;
export type ValidationConfig = typeof VALIDATION;

/**
 * Freeze all configuration objects to prevent runtime modifications
 */
Object.freeze(API_CONFIG);
Object.freeze(PAGINATION);
Object.freeze(CACHE);
Object.freeze(VALIDATION);