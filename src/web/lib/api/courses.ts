// @ts-check
import axios, { AxiosError } from 'axios'; // v1.4.0 - HTTP client
import { z } from 'zod'; // v3.21.0 - Runtime validation
import type { ApiResponse, PaginatedResponse } from '../../types/api';
import type { PaginationParams } from '../../types/common';

// Base URL for course-related endpoints
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL + '/api/v1/courses';

// Cache configuration
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes
const cache = new Map<string, { data: unknown; timestamp: number }>();

/**
 * Course data structure with comprehensive type information
 */
export interface Course {
  id: string;
  code: string;
  name: string;
  credits: number;
  description: string;
  institutionId: string;
  prerequisites: string[];
  metadata: Record<string, unknown>;
  validFrom: string;
  validTo: string | null;
  version: number;
}

/**
 * DTO for course creation
 */
export interface CreateCourseDto {
  code: string;
  name: string;
  credits: number;
  description: string;
  institutionId: string;
  prerequisites?: string[];
  metadata?: Record<string, unknown>;
  validFrom?: string;
  validTo?: string;
}

/**
 * DTO for course updates
 */
export interface UpdateCourseDto extends Partial<CreateCourseDto> {
  version: number; // For optimistic locking
}

/**
 * Course validation result structure
 */
export interface ValidationResult {
  isValid: boolean;
  requirements: {
    id: string;
    name: string;
    satisfied: boolean;
    details: string;
  }[];
  equivalencies: {
    courseId: string;
    institutionId: string;
    matchPercentage: number;
  }[];
}

// Zod schemas for runtime validation
const CourseSchema = z.object({
  id: z.string().uuid(),
  code: z.string().min(1),
  name: z.string().min(1),
  credits: z.number().positive(),
  description: z.string(),
  institutionId: z.string().uuid(),
  prerequisites: z.array(z.string().uuid()),
  metadata: z.record(z.unknown()),
  validFrom: z.string().datetime(),
  validTo: z.string().datetime().nullable(),
  version: z.number().int().nonnegative()
});

const ValidationResultSchema = z.object({
  isValid: z.boolean(),
  requirements: z.array(z.object({
    id: z.string().uuid(),
    name: z.string(),
    satisfied: z.boolean(),
    details: z.string()
  })),
  equivalencies: z.array(z.object({
    courseId: z.string().uuid(),
    institutionId: z.string().uuid(),
    matchPercentage: z.number().min(0).max(100)
  }))
});

/**
 * Fetches a paginated list of courses with optional filters
 * @param params Pagination parameters
 * @param filters Optional filters to apply
 * @returns Promise resolving to paginated course list
 */
export async function getCourses(
  params: PaginationParams,
  filters: Record<string, string> = {}
): Promise<PaginatedResponse<Course>> {
  const cacheKey = `courses:${JSON.stringify({ params, filters })}`;
  const cached = cache.get(cacheKey);

  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.data as PaginatedResponse<Course>;
  }

  try {
    const response = await axios.get<PaginatedResponse<Course>>(API_BASE_URL, {
      params: {
        ...params,
        ...filters
      },
      headers: {
        'Accept': 'application/json'
      }
    });

    // Validate response data
    const courses = response.data.data.map(course => CourseSchema.parse(course));
    const validatedResponse = {
      ...response.data,
      data: courses
    };

    // Update cache
    cache.set(cacheKey, {
      data: validatedResponse,
      timestamp: Date.now()
    });

    return validatedResponse;
  } catch (error) {
    if (error instanceof AxiosError && error.response?.status === 429) {
      // Handle rate limiting with exponential backoff
      await new Promise(resolve => setTimeout(resolve, 1000));
      return getCourses(params, filters);
    }
    throw error;
  }
}

/**
 * Fetches a single course by ID
 * @param id Course ID
 * @returns Promise resolving to course data
 */
export async function getCourseById(id: string): Promise<ApiResponse<Course>> {
  const cacheKey = `course:${id}`;
  const cached = cache.get(cacheKey);

  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.data as ApiResponse<Course>;
  }

  try {
    const response = await axios.get<ApiResponse<Course>>(`${API_BASE_URL}/${id}`);
    const validatedCourse = CourseSchema.parse(response.data.data);
    const validatedResponse = {
      ...response.data,
      data: validatedCourse
    };

    cache.set(cacheKey, {
      data: validatedResponse,
      timestamp: Date.now()
    });

    return validatedResponse;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 404) {
      throw new Error(`Course with ID ${id} not found`);
    }
    throw error;
  }
}

/**
 * Creates a new course
 * @param data Course creation data
 * @returns Promise resolving to created course
 */
export async function createCourse(data: CreateCourseDto): Promise<ApiResponse<Course>> {
  try {
    const response = await axios.post<ApiResponse<Course>>(
      API_BASE_URL,
      data,
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );

    const validatedCourse = CourseSchema.parse(response.data.data);
    return {
      ...response.data,
      data: validatedCourse
    };
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 409) {
      throw new Error(`Course with code ${data.code} already exists`);
    }
    throw error;
  }
}

/**
 * Updates an existing course
 * @param id Course ID
 * @param data Course update data
 * @returns Promise resolving to updated course
 */
export async function updateCourse(
  id: string,
  data: UpdateCourseDto
): Promise<ApiResponse<Course>> {
  try {
    const response = await axios.put<ApiResponse<Course>>(
      `${API_BASE_URL}/${id}`,
      data,
      {
        headers: {
          'Content-Type': 'application/json',
          'If-Match': `"${data.version}"` // Optimistic locking
        }
      }
    );

    const validatedCourse = CourseSchema.parse(response.data.data);
    
    // Invalidate cache
    cache.delete(`course:${id}`);
    Array.from(cache.keys())
      .filter(key => key.startsWith('courses:'))
      .forEach(key => cache.delete(key));

    return {
      ...response.data,
      data: validatedCourse
    };
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 412) {
        throw new Error('Course was modified by another user. Please refresh and try again.');
      }
      if (error.response?.status === 404) {
        throw new Error(`Course with ID ${id} not found`);
      }
    }
    throw error;
  }
}

/**
 * Validates course transfer eligibility
 * @param courseId Source course ID
 * @param targetInstitutionId Target institution ID
 * @returns Promise resolving to validation result
 */
export async function validateCourseTransfer(
  courseId: string,
  targetInstitutionId: string
): Promise<ApiResponse<ValidationResult>> {
  const cacheKey = `validation:${courseId}:${targetInstitutionId}`;
  const cached = cache.get(cacheKey);

  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.data as ApiResponse<ValidationResult>;
  }

  try {
    const response = await axios.post<ApiResponse<ValidationResult>>(
      `${API_BASE_URL}/${courseId}/validate`,
      {
        targetInstitutionId
      }
    );

    const validatedResult = ValidationResultSchema.parse(response.data.data);
    const validatedResponse = {
      ...response.data,
      data: validatedResult
    };

    cache.set(cacheKey, {
      data: validatedResponse,
      timestamp: Date.now()
    });

    return validatedResponse;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 503) {
      throw new Error('Validation service temporarily unavailable');
    }
    throw error;
  }
}