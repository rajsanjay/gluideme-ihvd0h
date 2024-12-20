/**
 * @fileoverview Frontend API client module for transfer requirements management
 * Provides typed functions for CRUD operations and validation of transfer requirements
 * @version 1.0.0
 */

import type { AxiosResponse, CancelToken } from 'axios'; // ^1.4.0
import type { 
  TransferRequirement, 
  RequirementValidationResult,
  RequirementType,
  RequirementStatus 
} from '../../types/requirements';
import type { PaginatedResponse } from '../../types/api';
import apiClient from '../../config/api';

// API endpoints for transfer requirements
const API_ENDPOINTS = {
  REQUIREMENTS: '/api/v1/requirements/',
  VALIDATE_COURSES: '/api/v1/requirements/{id}/validate-courses/',
  REQUIREMENT_VERSIONS: '/api/v1/requirements/{id}/versions/',
  REQUIREMENT_METADATA: '/api/v1/requirements/{id}/metadata/'
} as const;

// Cache configuration for requirements data
const CACHE_CONFIG = {
  REQUIREMENTS_TTL: 300000, // 5 minutes
  METADATA_TTL: 600000 // 10 minutes
} as const;

/**
 * Filter parameters for requirements search
 */
export interface RequirementFilters {
  institutionId?: string;
  majorCode?: string;
  type?: RequirementType;
  status?: RequirementStatus;
  effectiveDate?: string;
  search?: string;
}

/**
 * Options for fetching requirement details
 */
export interface RequirementDetailOptions {
  includeVersions?: boolean;
  includeMetadata?: boolean;
  cancelToken?: CancelToken;
}

/**
 * Fetches a paginated list of transfer requirements with optional filtering
 * @param params - Pagination and filtering parameters
 * @returns Promise resolving to paginated requirements response
 */
export const getRequirements = async (params: {
  page?: number;
  limit?: number;
  sort?: string;
  filters?: RequirementFilters;
  cancelToken?: CancelToken;
}): Promise<AxiosResponse<PaginatedResponse<TransferRequirement>>> => {
  const queryParams = {
    page: params.page || 1,
    limit: params.limit || 10,
    sort: params.sort,
    ...params.filters
  };

  return apiClient.get<PaginatedResponse<TransferRequirement>>(
    API_ENDPOINTS.REQUIREMENTS,
    {
      params: queryParams,
      cancelToken: params.cancelToken
    }
  );
};

/**
 * Retrieves a single transfer requirement by ID
 * @param id - Requirement identifier
 * @param options - Additional fetch options
 * @returns Promise resolving to requirement details
 */
export const getRequirementById = async (
  id: string,
  options: RequirementDetailOptions = {}
): Promise<AxiosResponse<TransferRequirement>> => {
  const { includeVersions, includeMetadata, cancelToken } = options;
  
  return apiClient.get<TransferRequirement>(
    `${API_ENDPOINTS.REQUIREMENTS}${id}/`,
    {
      params: {
        include_versions: includeVersions,
        include_metadata: includeMetadata
      },
      cancelToken
    }
  );
};

/**
 * Creates a new transfer requirement
 * @param requirement - Transfer requirement data
 * @returns Promise resolving to created requirement
 */
export const createRequirement = async (
  requirement: Partial<TransferRequirement>
): Promise<AxiosResponse<TransferRequirement>> => {
  return apiClient.post<TransferRequirement>(
    API_ENDPOINTS.REQUIREMENTS,
    requirement
  );
};

/**
 * Updates an existing transfer requirement
 * @param id - Requirement identifier
 * @param updates - Partial requirement updates
 * @returns Promise resolving to updated requirement
 */
export const updateRequirement = async (
  id: string,
  updates: Partial<TransferRequirement>
): Promise<AxiosResponse<TransferRequirement>> => {
  return apiClient.put<TransferRequirement>(
    `${API_ENDPOINTS.REQUIREMENTS}${id}/`,
    updates
  );
};

/**
 * Validates courses against a transfer requirement
 * @param id - Requirement identifier
 * @param courses - Array of course codes to validate
 * @returns Promise resolving to validation results
 */
export const validateCourses = async (
  id: string,
  courses: string[]
): Promise<AxiosResponse<RequirementValidationResult>> => {
  return apiClient.post<RequirementValidationResult>(
    API_ENDPOINTS.VALIDATE_COURSES.replace('{id}', id),
    { courses }
  );
};

/**
 * Retrieves version history for a requirement
 * @param id - Requirement identifier
 * @returns Promise resolving to version history
 */
export const getRequirementVersions = async (
  id: string
): Promise<AxiosResponse<TransferRequirement[]>> => {
  return apiClient.get<TransferRequirement[]>(
    API_ENDPOINTS.REQUIREMENT_VERSIONS.replace('{id}', id)
  );
};

/**
 * Updates the status of a transfer requirement
 * @param id - Requirement identifier
 * @param status - New requirement status
 * @returns Promise resolving to updated requirement
 */
export const updateRequirementStatus = async (
  id: string,
  status: RequirementStatus
): Promise<AxiosResponse<TransferRequirement>> => {
  return apiClient.put<TransferRequirement>(
    `${API_ENDPOINTS.REQUIREMENTS}${id}/status/`,
    { status }
  );
};

/**
 * Deletes a transfer requirement
 * @param id - Requirement identifier
 * @returns Promise resolving to void
 */
export const deleteRequirement = async (
  id: string
): Promise<AxiosResponse<void>> => {
  return apiClient.delete(
    `${API_ENDPOINTS.REQUIREMENTS}${id}/`
  );
};

/**
 * Retrieves metadata for a requirement
 * @param id - Requirement identifier
 * @returns Promise resolving to requirement metadata
 */
export const getRequirementMetadata = async (
  id: string
): Promise<AxiosResponse<Record<string, unknown>>> => {
  return apiClient.get(
    API_ENDPOINTS.REQUIREMENT_METADATA.replace('{id}', id)
  );
};