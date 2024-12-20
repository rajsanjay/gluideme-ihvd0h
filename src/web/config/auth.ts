import { UserRole } from '../types/auth';

/**
 * Core authentication configuration constants
 * Defines token management and security settings
 */
export const AUTH_CONFIG = {
  // Storage keys for browser storage
  TOKEN_STORAGE_KEY: 'trms_auth_token',
  USER_STORAGE_KEY: 'trms_user',

  // Token durations in seconds (from technical spec 7.1.3)
  ACCESS_TOKEN_DURATION: 15 * 60, // 15 minutes
  REFRESH_TOKEN_DURATION: 7 * 24 * 60 * 60, // 7 days
  
  // Threshold to trigger token refresh (75% of access token duration)
  REFRESH_THRESHOLD: 11 * 60, // 11 minutes

  // CSRF protection configuration
  CSRF_HEADER_NAME: 'X-CSRF-Token',
  CSRF_COOKIE_NAME: 'csrf_token'
} as const;

/**
 * Role-based access control configuration
 * Defines granular permissions for each user role based on technical spec 7.1.2
 */
export const ROLE_PERMISSIONS = {
  admin: {
    requirements: {
      read: true,
      create: true,
      update: true,
      delete: true
    },
    studentData: {
      read: true,
      update: true,
      delete: true
    },
    reports: {
      read: true,
      generate: true,
      export: true
    },
    systemConfig: {
      read: true,
      update: true
    }
  },

  institution_admin: {
    requirements: {
      read: true,
      create: 'own_institution',
      update: 'own_institution',
      delete: 'own_institution'
    },
    studentData: {
      read: 'own_institution',
      update: 'own_institution',
      delete: false
    },
    reports: {
      read: 'own_institution',
      generate: 'own_institution',
      export: 'own_institution'
    },
    systemConfig: {
      read: false,
      update: false
    }
  },

  counselor: {
    requirements: {
      read: true,
      create: false,
      update: false,
      delete: false
    },
    studentData: {
      read: true,
      update: true,
      delete: false
    },
    reports: {
      read: true,
      generate: false,
      export: false
    },
    systemConfig: {
      read: false,
      update: false
    }
  },

  student: {
    requirements: {
      read: true,
      create: false,
      update: false,
      delete: false
    },
    studentData: {
      read: 'own_data',
      update: 'own_data',
      delete: false
    },
    reports: {
      read: false,
      generate: false,
      export: false
    },
    systemConfig: {
      read: false,
      update: false
    }
  },

  guest: {
    requirements: {
      read: 'public_only',
      create: false,
      update: false,
      delete: false
    },
    studentData: {
      read: false,
      update: false,
      delete: false
    },
    reports: {
      read: false,
      generate: false,
      export: false
    },
    systemConfig: {
      read: false,
      update: false
    }
  }
} as const;

/**
 * Authentication API endpoint paths
 * Centralized configuration for all authentication-related operations
 */
export const AUTH_ENDPOINTS = {
  LOGIN: '/api/v1/auth/login',
  REGISTER: '/api/v1/auth/register',
  LOGOUT: '/api/v1/auth/logout',
  REFRESH_TOKEN: '/api/v1/auth/refresh',
  VERIFY_TOKEN: '/api/v1/auth/verify',
  CHANGE_PASSWORD: '/api/v1/auth/password'
} as const;

/**
 * Authentication error messages
 * Standardized error messages for consistent error handling
 */
export const AUTH_ERRORS = {
  INVALID_CREDENTIALS: 'Invalid email or password',
  TOKEN_EXPIRED: 'Your session has expired. Please log in again',
  UNAUTHORIZED: 'You are not authorized to perform this action',
  REGISTRATION_FAILED: 'Registration failed. Please try again',
  INVALID_TOKEN: 'Invalid authentication token',
  SESSION_EXPIRED: 'Your session has expired. Please log in again',
  REFRESH_FAILED: 'Unable to refresh authentication token',
  CSRF_VALIDATION_FAILED: 'CSRF token validation failed'
} as const;