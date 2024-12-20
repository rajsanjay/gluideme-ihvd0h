/**
 * @fileoverview Configures and exports the Axios HTTP client instance with comprehensive configuration
 * for API communication, including request/response interceptors, error handling, retry logic,
 * monitoring, and security features.
 * @version 1.0.0
 */

import axios, { AxiosError, AxiosInstance, AxiosResponse } from 'axios'; // ^1.4.0
import axiosRetry from 'axios-retry'; // ^3.5.0
import { setupCache, buildMemoryStorage } from 'axios-cache-adapter'; // ^2.7.3
import { API_CONFIG } from './constants';
import { ApiError, ValidationError, apiErrorSchema } from '../types/api';

/**
 * Default Axios configuration
 */
const AXIOS_DEFAULTS = {
  baseURL: API_CONFIG.BASE_URL,
  timeout: API_CONFIG.TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Accept-Encoding': 'gzip, deflate, br'
  },
  decompress: true
};

/**
 * Retry configuration with exponential backoff
 */
const RETRY_CONFIG = {
  retries: API_CONFIG.RETRY_ATTEMPTS,
  retryDelay: (retryCount: number) => {
    return Math.min(1000 * Math.pow(2, retryCount), 10000);
  },
  retryCondition: (error: AxiosError) => {
    return axiosRetry.isNetworkOrIdempotentRequestError(error) || 
           (error.response?.status === 503);
  }
};

/**
 * Cache configuration
 */
const CACHE_CONFIG = {
  maxAge: 15 * 60 * 1000, // 15 minutes
  exclude: { query: false },
  clearOnError: true,
  storage: buildMemoryStorage()
};

/**
 * Processes and standardizes API errors
 * @param error - The axios error object
 * @returns Standardized API error object
 */
const handleApiError = (error: AxiosError): ApiError => {
  const defaultError: ApiError = {
    code: 'INTERNAL_SERVER_ERROR',
    message: 'An unexpected error occurred',
    errors: []
  };

  if (!error.response) {
    return {
      ...defaultError,
      code: 'INTERNAL_SERVER_ERROR',
      message: 'Network error occurred'
    };
  }

  try {
    const errorData = error.response.data;
    const validatedError = apiErrorSchema.parse(errorData);
    return validatedError;
  } catch (validationError) {
    console.error('Error response validation failed:', validationError);
    return defaultError;
  }
};

/**
 * Configures request monitoring and metrics collection
 * @param instance - Axios instance to configure monitoring for
 */
const setupRequestMonitoring = (instance: AxiosInstance): void => {
  let requestsInFlight = 0;
  const requestTimes: number[] = [];

  instance.interceptors.request.use((config) => {
    requestsInFlight++;
    config.metadata = { startTime: Date.now() };
    return config;
  });

  instance.interceptors.response.use(
    (response) => {
      requestsInFlight--;
      const duration = Date.now() - (response.config.metadata?.startTime || 0);
      requestTimes.push(duration);
      
      // Report metrics if duration exceeds threshold
      if (duration > 500) {
        console.warn(`Slow request detected: ${response.config.url} (${duration}ms)`);
      }
      
      return response;
    },
    (error) => {
      requestsInFlight--;
      return Promise.reject(error);
    }
  );
};

/**
 * Creates and configures an Axios instance with enhanced features
 */
const createAxiosInstance = (): AxiosInstance => {
  // Setup cache adapter
  const cache = setupCache({
    ...CACHE_CONFIG,
    debug: process.env.NODE_ENV === 'development'
  });

  // Create axios instance with cache adapter
  const instance = axios.create({
    ...AXIOS_DEFAULTS,
    adapter: cache.adapter
  });

  // Configure retry logic
  axiosRetry(instance, RETRY_CONFIG);

  // Request interceptor
  instance.interceptors.request.use(
    (config) => {
      // Add auth token if available
      const token = localStorage.getItem('authToken');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  // Response interceptor
  instance.interceptors.response.use(
    (response: AxiosResponse) => {
      return response;
    },
    (error: AxiosError) => {
      const processedError = handleApiError(error);
      return Promise.reject(processedError);
    }
  );

  // Setup monitoring
  setupRequestMonitoring(instance);

  return instance;
};

/**
 * Export configured axios instance
 */
export const apiClient = createAxiosInstance();

/**
 * Export type definitions for better type safety
 */
export type { ApiError, ValidationError };

export default apiClient;