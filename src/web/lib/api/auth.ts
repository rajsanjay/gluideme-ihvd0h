/**
 * @fileoverview Authentication API functions for user login, registration, logout and token refresh
 * Implements JWT-based authentication with enhanced security features and comprehensive error handling
 * @version 1.0.0
 */

import { AxiosResponse } from 'axios'; // ^1.4.0
import apiClient from '../../config/api';
import { LoginCredentials, RegisterData, AuthResponse, AuthTokens, AuthSchemas } from '../../types/auth';
import { VALIDATION } from '../../config/constants';

/**
 * Authentication endpoints
 */
const AUTH_ENDPOINTS = {
  LOGIN: '/api/v1/auth/login',
  REGISTER: '/api/v1/auth/register',
  LOGOUT: '/api/v1/auth/logout',
  REFRESH: '/api/v1/auth/refresh'
} as const;

/**
 * Token storage keys
 */
const TOKEN_STORAGE = {
  ACCESS_TOKEN: 'auth_access_token',
  REFRESH_TOKEN: 'auth_refresh_token'
} as const;

/**
 * Stores authentication tokens securely
 * @param tokens - Authentication tokens to store
 */
const storeTokens = (tokens: AuthTokens): void => {
  localStorage.setItem(TOKEN_STORAGE.ACCESS_TOKEN, tokens.accessToken);
  localStorage.setItem(TOKEN_STORAGE.REFRESH_TOKEN, tokens.refreshToken);
};

/**
 * Clears stored authentication tokens
 */
const clearTokens = (): void => {
  localStorage.removeItem(TOKEN_STORAGE.ACCESS_TOKEN);
  localStorage.removeItem(TOKEN_STORAGE.REFRESH_TOKEN);
};

/**
 * Authenticates user with email and password
 * @param credentials - User login credentials
 * @returns Authentication response with user data and tokens
 * @throws ApiError on authentication failure
 */
export const login = async (credentials: LoginCredentials): Promise<AuthResponse> => {
  try {
    // Validate credentials using zod schema
    const validatedCredentials = AuthSchemas.loginSchema.parse(credentials);

    // Attempt login
    const response: AxiosResponse<AuthResponse> = await apiClient.post(
      AUTH_ENDPOINTS.LOGIN,
      validatedCredentials
    );

    // Store tokens securely
    storeTokens(response.data.tokens);

    return response.data;
  } catch (error) {
    // Log authentication failure for monitoring
    console.error('Authentication failed:', error);
    throw error;
  }
};

/**
 * Registers new user with provided details
 * @param data - User registration data
 * @returns Authentication response with user data and tokens
 * @throws ApiError on registration failure
 */
export const register = async (data: RegisterData): Promise<AuthResponse> => {
  try {
    // Validate registration data using zod schema
    const validatedData = AuthSchemas.registerSchema.parse(data);

    // Additional password strength validation
    if (data.password.length < VALIDATION.MIN_PASSWORD_LENGTH) {
      throw new Error(`Password must be at least ${VALIDATION.MIN_PASSWORD_LENGTH} characters`);
    }

    // Attempt registration
    const response: AxiosResponse<AuthResponse> = await apiClient.post(
      AUTH_ENDPOINTS.REGISTER,
      validatedData
    );

    // Store tokens securely
    storeTokens(response.data.tokens);

    return response.data;
  } catch (error) {
    // Log registration failure for monitoring
    console.error('Registration failed:', error);
    throw error;
  }
};

/**
 * Logs out current user and invalidates their tokens
 * @throws ApiError on logout failure
 */
export const logout = async (): Promise<void> => {
  try {
    // Get refresh token for revocation
    const refreshToken = localStorage.getItem(TOKEN_STORAGE.REFRESH_TOKEN);

    if (refreshToken) {
      // Revoke refresh token on server
      await apiClient.delete(AUTH_ENDPOINTS.LOGOUT, {
        data: { refreshToken }
      });
    }

    // Clear local token storage
    clearTokens();
  } catch (error) {
    // Log logout failure but still clear local tokens
    console.error('Logout failed:', error);
    clearTokens();
    throw error;
  }
};

// Queue for pending token refresh requests
let refreshQueue: Promise<AuthTokens> | null = null;

/**
 * Refreshes access token using refresh token
 * @param refreshToken - Current refresh token
 * @returns New authentication tokens
 * @throws ApiError on refresh failure
 */
export const refreshToken = async (refreshToken: string): Promise<AuthTokens> => {
  try {
    // If a refresh is already in progress, return the same promise
    if (refreshQueue) {
      return refreshQueue;
    }

    // Create new refresh request
    refreshQueue = (async () => {
      try {
        const response: AxiosResponse<{ tokens: AuthTokens }> = await apiClient.post(
          AUTH_ENDPOINTS.REFRESH,
          { refreshToken }
        );

        // Store new tokens
        storeTokens(response.data.tokens);

        return response.data.tokens;
      } finally {
        // Clear queue after completion/error
        refreshQueue = null;
      }
    })();

    return refreshQueue;
  } catch (error) {
    // Log refresh failure and clear tokens on fatal error
    console.error('Token refresh failed:', error);
    clearTokens();
    throw error;
  }
};