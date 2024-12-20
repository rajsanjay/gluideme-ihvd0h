// @ts-check
import { z } from 'zod'; // v3.21.0 - Runtime type validation
import { User } from './api';

/**
 * Valid user roles in the system with strict type checking
 */
export type UserRole = 'admin' | 'institution_admin' | 'counselor' | 'student' | 'guest';

/**
 * Possible token-related error conditions
 */
export type TokenError = 'expired' | 'invalid' | 'missing' | 'refresh_required';

/**
 * Login credentials interface with email and password
 */
export interface LoginCredentials {
  /** User's email address */
  email: string;
  /** User's password (will be securely hashed) */
  password: string;
}

/**
 * Registration data interface with additional fields
 */
export interface RegisterData {
  /** User's email address */
  email: string;
  /** User's password (will be securely hashed) */
  password: string;
  /** User's role in the system */
  role: UserRole;
  /** Optional institution ID for institution-specific roles */
  institutionId: string | null;
}

/**
 * JWT token pair structure with expiration tracking
 */
export interface AuthTokens {
  /** JWT access token for API authorization */
  accessToken: string;
  /** Refresh token for obtaining new access tokens */
  refreshToken: string;
  /** Access token expiration time in seconds */
  expiresIn: number;
}

/**
 * Complete authentication response structure
 */
export interface AuthResponse {
  /** Authenticated user information */
  user: User;
  /** JWT token pair */
  tokens: AuthTokens;
}

/**
 * Comprehensive authentication state management
 */
export interface AuthState {
  /** Flag indicating if user is currently authenticated */
  isAuthenticated: boolean;
  /** Current user information (null if not authenticated) */
  user: User | null;
  /** Current access token (null if not authenticated) */
  accessToken: string | null;
  /** Flag indicating authentication operation in progress */
  loading: boolean;
  /** Current authentication error state */
  error: TokenError | null;
}

/**
 * Zod validation schemas for authentication forms
 */
export const AuthSchemas = {
  /**
   * Login form validation schema
   */
  loginSchema: z.object({
    email: z.string()
      .email('Invalid email format')
      .min(1, 'Email is required'),
    password: z.string()
      .min(8, 'Password must be at least 8 characters')
      .max(100, 'Password is too long')
  }),

  /**
   * Registration form validation schema
   */
  registerSchema: z.object({
    email: z.string()
      .email('Invalid email format')
      .min(1, 'Email is required'),
    password: z.string()
      .min(8, 'Password must be at least 8 characters')
      .max(100, 'Password is too long')
      .regex(
        /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$/,
        'Password must include uppercase, lowercase, number and special character'
      ),
    role: z.enum(['admin', 'institution_admin', 'counselor', 'student', 'guest'] as const),
    institutionId: z.string().uuid().nullable()
  })
};