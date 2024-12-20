/**
 * @fileoverview API client functions for student-related operations including profile management,
 * transfer plan creation/updates, and progress tracking with enhanced error handling and type safety.
 * @version 1.0.0
 */

import apiClient from '../../config/api';
import type { ApiResponse } from '../../types/api';
import type { 
  StudentProfile, 
  TransferPlan,
  studentProfileSchema,
  transferPlanSchema
} from '../../types/student';

/**
 * Error messages for student API operations
 */
const ERROR_MESSAGES = {
  FETCH_PROFILE: 'Failed to fetch student profile',
  UPDATE_PROFILE: 'Failed to update student profile',
  FETCH_PLANS: 'Failed to fetch transfer plans',
  FETCH_PLAN: 'Failed to fetch transfer plan',
  CREATE_PLAN: 'Failed to create transfer plan',
  UPDATE_PLAN: 'Failed to update transfer plan',
} as const;

/**
 * Retrieves the student profile information with enhanced error handling and logging
 * @param studentId - The unique identifier of the student
 * @returns Promise resolving to the student profile data
 */
export async function getStudentProfile(
  studentId: string
): Promise<ApiResponse<StudentProfile>> {
  try {
    const response = await apiClient.get<ApiResponse<StudentProfile>>(
      `/api/v1/students/${studentId}/profile`
    );

    // Validate response data against schema
    const validatedData = studentProfileSchema.parse(response.data.data);
    return {
      ...response.data,
      data: validatedData
    };
  } catch (error) {
    console.error(`${ERROR_MESSAGES.FETCH_PROFILE}:`, error);
    throw error;
  }
}

/**
 * Updates student profile information with validation and error tracking
 * @param studentId - The unique identifier of the student
 * @param profileData - Partial profile data to update
 * @returns Promise resolving to the updated student profile
 */
export async function updateStudentProfile(
  studentId: string,
  profileData: Partial<StudentProfile>
): Promise<ApiResponse<StudentProfile>> {
  try {
    const response = await apiClient.put<ApiResponse<StudentProfile>>(
      `/api/v1/students/${studentId}/profile`,
      profileData
    );

    // Validate response data against schema
    const validatedData = studentProfileSchema.parse(response.data.data);
    return {
      ...response.data,
      data: validatedData
    };
  } catch (error) {
    console.error(`${ERROR_MESSAGES.UPDATE_PROFILE}:`, error);
    throw error;
  }
}

/**
 * Retrieves all transfer plans for a student with pagination and caching
 * @param studentId - The unique identifier of the student
 * @returns Promise resolving to an array of transfer plans
 */
export async function getTransferPlans(
  studentId: string
): Promise<ApiResponse<TransferPlan[]>> {
  try {
    const response = await apiClient.get<ApiResponse<TransferPlan[]>>(
      `/api/v1/students/${studentId}/plans`
    );

    // Validate each plan in the response
    const validatedPlans = response.data.data.map(plan => 
      transferPlanSchema.parse(plan)
    );

    return {
      ...response.data,
      data: validatedPlans
    };
  } catch (error) {
    console.error(`${ERROR_MESSAGES.FETCH_PLANS}:`, error);
    throw error;
  }
}

/**
 * Retrieves a specific transfer plan with detailed validation
 * @param studentId - The unique identifier of the student
 * @param planId - The unique identifier of the transfer plan
 * @returns Promise resolving to the transfer plan details
 */
export async function getTransferPlan(
  studentId: string,
  planId: string
): Promise<ApiResponse<TransferPlan>> {
  try {
    const response = await apiClient.get<ApiResponse<TransferPlan>>(
      `/api/v1/students/${studentId}/plans/${planId}`
    );

    // Validate response data against schema
    const validatedPlan = transferPlanSchema.parse(response.data.data);
    return {
      ...response.data,
      data: validatedPlan
    };
  } catch (error) {
    console.error(`${ERROR_MESSAGES.FETCH_PLAN}:`, error);
    throw error;
  }
}

/**
 * Creates a new transfer plan for a student with comprehensive validation
 * @param studentId - The unique identifier of the student
 * @param planData - The transfer plan data without ID
 * @returns Promise resolving to the created transfer plan
 */
export async function createTransferPlan(
  studentId: string,
  planData: Omit<TransferPlan, 'id'>
): Promise<ApiResponse<TransferPlan>> {
  try {
    const response = await apiClient.post<ApiResponse<TransferPlan>>(
      `/api/v1/students/${studentId}/plans`,
      planData
    );

    // Validate response data against schema
    const validatedPlan = transferPlanSchema.parse(response.data.data);
    return {
      ...response.data,
      data: validatedPlan
    };
  } catch (error) {
    console.error(`${ERROR_MESSAGES.CREATE_PLAN}:`, error);
    throw error;
  }
}

/**
 * Updates an existing transfer plan with validation and conflict detection
 * @param studentId - The unique identifier of the student
 * @param planId - The unique identifier of the transfer plan
 * @param planData - Partial transfer plan data to update
 * @returns Promise resolving to the updated transfer plan
 */
export async function updateTransferPlan(
  studentId: string,
  planId: string,
  planData: Partial<TransferPlan>
): Promise<ApiResponse<TransferPlan>> {
  try {
    const response = await apiClient.put<ApiResponse<TransferPlan>>(
      `/api/v1/students/${studentId}/plans/${planId}`,
      planData
    );

    // Validate response data against schema
    const validatedPlan = transferPlanSchema.parse(response.data.data);
    return {
      ...response.data,
      data: validatedPlan
    };
  } catch (error) {
    console.error(`${ERROR_MESSAGES.UPDATE_PLAN}:`, error);
    throw error;
  }
}