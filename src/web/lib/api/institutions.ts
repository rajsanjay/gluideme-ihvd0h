// @ts-check
import axios, { AxiosError } from 'axios'; // v1.4.0 - HTTP client with interceptors
import { z } from 'zod'; // v3.21.0 - Runtime type validation
import type { 
  ApiResponse, 
  ApiError, 
  PaginatedResponse 
} from '../../types/api';
import type { 
  PaginationParams,
  FilterParams,
  SortParams 
} from '../../types/common';

// API configuration constants
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL + '/api/v1/institutions';
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000;

/**
 * Zod schema for institution contact information validation
 */
const contactInfoSchema = z.object({
  email: z.string().email(),
  phone: z.string().regex(/^\+?[1-9]\d{1,14}$/, 'Invalid phone number format'),
  address: z.string().min(5).max(500)
});

/**
 * Comprehensive Zod schema for institution data validation
 */
export const institutionSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1).max(255),
  code: z.string().regex(/^[A-Z0-9]{2,10}$/, 'Invalid institution code format'),
  type: z.enum(['university', 'community_college', 'private']),
  status: z.enum(['active', 'inactive', 'pending']),
  contact_info: contactInfoSchema,
  metadata: z.record(z.string(), z.unknown()).optional(),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime()
});

/**
 * Institution type derived from the schema
 */
export type Institution = z.infer<typeof institutionSchema>;

/**
 * Interface for institution creation payload
 */
export type CreateInstitutionPayload = Omit<Institution, 'id' | 'created_at' | 'updated_at'>;

/**
 * Interface for institution update payload
 */
export type UpdateInstitutionPayload = Partial<CreateInstitutionPayload>;

/**
 * Available filter fields for institution queries
 */
export interface InstitutionFilters extends FilterParams {
  type?: 'university' | 'community_college' | 'private';
  status?: 'active' | 'inactive' | 'pending';
  search?: string;
}

/**
 * Error class for institution-specific API errors
 */
export class InstitutionApiError extends Error {
  constructor(
    message: string,
    public code: string,
    public status: number,
    public errors?: ApiError['errors']
  ) {
    super(message);
    this.name = 'InstitutionApiError';
  }
}

/**
 * Fetches a paginated list of institutions with optional filters
 * @param params - Pagination, sorting, and filtering parameters
 * @param filters - Optional filters for institution query
 * @returns Promise resolving to paginated institution data
 * @throws {InstitutionApiError} When API request fails
 */
export async function getInstitutions(
  params: PaginationParams & SortParams,
  filters?: InstitutionFilters
): Promise<PaginatedResponse<Institution>> {
  try {
    const response = await axios.get<ApiResponse<PaginatedResponse<Institution>>>(
      API_BASE_URL,
      {
        params: {
          ...params,
          ...filters,
        },
        timeout: 5000,
        retries: MAX_RETRIES,
        retryDelay: RETRY_DELAY,
      }
    );

    // Validate response data against schema
    const institutions = response.data.data.data.map(institution => 
      institutionSchema.parse(institution)
    );

    return {
      ...response.data.data,
      data: institutions
    };
  } catch (error) {
    handleApiError(error);
  }
}

/**
 * Creates a new institution
 * @param payload - Institution creation payload
 * @returns Promise resolving to created institution
 * @throws {InstitutionApiError} When API request fails
 */
export async function createInstitution(
  payload: CreateInstitutionPayload
): Promise<Institution> {
  try {
    // Validate payload before sending
    const validatedPayload = institutionSchema.omit({ 
      id: true, 
      created_at: true, 
      updated_at: true 
    }).parse(payload);

    const response = await axios.post<ApiResponse<Institution>>(
      API_BASE_URL,
      validatedPayload,
      {
        timeout: 5000,
        retries: MAX_RETRIES,
        retryDelay: RETRY_DELAY,
      }
    );

    return institutionSchema.parse(response.data.data);
  } catch (error) {
    handleApiError(error);
  }
}

/**
 * Updates an existing institution
 * @param id - Institution UUID
 * @param payload - Partial institution update payload
 * @returns Promise resolving to updated institution
 * @throws {InstitutionApiError} When API request fails
 */
export async function updateInstitution(
  id: string,
  payload: UpdateInstitutionPayload
): Promise<Institution> {
  try {
    // Validate payload before sending
    const validatedPayload = institutionSchema.partial().parse(payload);

    const response = await axios.put<ApiResponse<Institution>>(
      `${API_BASE_URL}/${id}`,
      validatedPayload,
      {
        timeout: 5000,
        retries: MAX_RETRIES,
        retryDelay: RETRY_DELAY,
      }
    );

    return institutionSchema.parse(response.data.data);
  } catch (error) {
    handleApiError(error);
  }
}

/**
 * Retrieves a single institution by ID
 * @param id - Institution UUID
 * @returns Promise resolving to institution data
 * @throws {InstitutionApiError} When API request fails
 */
export async function getInstitution(id: string): Promise<Institution> {
  try {
    const response = await axios.get<ApiResponse<Institution>>(
      `${API_BASE_URL}/${id}`,
      {
        timeout: 5000,
        retries: MAX_RETRIES,
        retryDelay: RETRY_DELAY,
      }
    );

    return institutionSchema.parse(response.data.data);
  } catch (error) {
    handleApiError(error);
  }
}

/**
 * Deletes an institution by ID
 * @param id - Institution UUID
 * @returns Promise resolving to void on success
 * @throws {InstitutionApiError} When API request fails
 */
export async function deleteInstitution(id: string): Promise<void> {
  try {
    await axios.delete(`${API_BASE_URL}/${id}`, {
      timeout: 5000,
      retries: MAX_RETRIES,
      retryDelay: RETRY_DELAY,
    });
  } catch (error) {
    handleApiError(error);
  }
}

/**
 * Centralized error handler for institution API requests
 * @param error - Error object from axios request
 * @throws {InstitutionApiError} Transformed API error
 */
function handleApiError(error: unknown): never {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiResponse<ApiError>>;
    const status = axiosError.response?.status ?? 500;
    const errorData = axiosError.response?.data?.data;

    throw new InstitutionApiError(
      errorData?.message ?? 'An unexpected error occurred',
      errorData?.code ?? 'INTERNAL_SERVER_ERROR',
      status,
      errorData?.errors
    );
  }

  throw new InstitutionApiError(
    'An unexpected error occurred',
    'INTERNAL_SERVER_ERROR',
    500
  );
}