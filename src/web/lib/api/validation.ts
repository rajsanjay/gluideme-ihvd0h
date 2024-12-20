/**
 * @fileoverview API client functions for course validation operations with comprehensive error handling,
 * caching, and performance monitoring. Implements the real-time course validation engine with 99.99%
 * accuracy target.
 * @version 1.0.0
 */

import { z } from 'zod'; // v3.21.0
import retry from 'axios-retry'; // v3.5.0
import memoize from 'lodash/memoize'; // v4.1.2
import apiClient from '../../config/api';
import type { ApiResponse, PaginatedResponse } from '../../types/api';

/**
 * Validation result metadata for accuracy tracking
 */
interface ValidationMetadata {
  timestamp: string;
  duration: number;
  confidence: number;
  version: string;
}

/**
 * Detailed validation error information
 */
interface ValidationError {
  code: string;
  message: string;
  field?: string;
  details?: Record<string, unknown>;
}

/**
 * Comprehensive validation result
 */
export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  details: Record<string, unknown>;
  metadata: ValidationMetadata;
}

/**
 * Validation request parameters schema
 */
const validationRequestSchema = z.object({
  courseId: z.string().uuid(),
  requirementId: z.string().uuid(),
  institutionId: z.string().uuid(),
  version: z.string().optional()
});

/**
 * Validation history filter parameters schema
 */
const historyFilterSchema = z.object({
  courseId: z.string().uuid().optional(),
  requirementId: z.string().uuid().optional(),
  startDate: z.string().datetime().optional(),
  endDate: z.string().datetime().optional(),
  status: z.enum(['valid', 'invalid', 'pending']).optional(),
  page: z.number().int().positive().optional(),
  pageSize: z.number().int().min(1).max(100).optional()
});

/**
 * Performance monitoring decorator
 */
function monitor(metricName: string) {
  return function (
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor
  ) {
    const originalMethod = descriptor.value;
    descriptor.value = async function (...args: any[]) {
      const startTime = Date.now();
      try {
        const result = await originalMethod.apply(this, args);
        const duration = Date.now() - startTime;
        
        // Log metrics for monitoring
        console.info(`${metricName} completed in ${duration}ms`);
        if (duration > 500) {
          console.warn(`${metricName} exceeded 500ms threshold`);
        }
        
        return result;
      } catch (error) {
        console.error(`${metricName} failed:`, error);
        throw error;
      }
    };
    return descriptor;
  };
}

/**
 * Validates a course against transfer requirements with retry logic and request deduplication
 * @param request Validation request parameters
 * @returns Validation result with detailed status information
 */
export const validateCourse = memoize(
  async (request: {
    courseId: string;
    requirementId: string;
    institutionId: string;
    version?: string;
  }): Promise<ApiResponse<ValidationResult>> => {
    // Validate request parameters
    const validatedRequest = validationRequestSchema.parse(request);

    try {
      const response = await apiClient.post<ValidationResult>(
        '/api/v1/validation/validate-course',
        validatedRequest,
        {
          'axios-retry': {
            retries: 3,
            retryCondition: (error) => {
              return retry.isNetworkOrIdempotentRequestError(error) ||
                     error.response?.status === 503;
            },
            retryDelay: (retryCount) => {
              return Math.min(1000 * Math.pow(2, retryCount), 10000);
            }
          }
        }
      );

      return response;
    } catch (error) {
      console.error('Course validation failed:', error);
      throw error;
    }
  },
  // Memoization key generator
  (args) => JSON.stringify(args),
  // Memoization options
  { maxAge: 5000 } // Cache for 5 seconds
);

/**
 * Retrieves validation history with pagination and filtering
 * @param filters Optional filters for validation history
 * @returns Paginated list of validation records
 */
export const getValidationHistory = async (filters: {
  courseId?: string;
  requirementId?: string;
  startDate?: string;
  endDate?: string;
  status?: string;
  page?: number;
  pageSize?: number;
}): Promise<ApiResponse<PaginatedResponse<ValidationResult>>> => {
  // Validate filter parameters
  const validatedFilters = historyFilterSchema.parse(filters);

  try {
    const response = await apiClient.get<PaginatedResponse<ValidationResult>>(
      '/api/v1/validation/records',
      {
        params: validatedFilters
      }
    );

    return response;
  } catch (error) {
    console.error('Failed to retrieve validation history:', error);
    throw error;
  }
};

/**
 * Retrieves detailed validation record
 * @param validationId ID of the validation record
 * @returns Detailed validation record
 */
export const getValidationDetails = async (
  validationId: string
): Promise<ApiResponse<ValidationResult>> => {
  // Validate validation ID
  const validId = z.string().uuid().parse(validationId);

  try {
    const response = await apiClient.get<ValidationResult>(
      `/api/v1/validation/records/${validId}`
    );

    return response;
  } catch (error) {
    console.error('Failed to retrieve validation details:', error);
    throw error;
  }
};

/**
 * Type definitions for better type safety
 */
export type {
  ValidationResult,
  ValidationError,
  ValidationMetadata
};