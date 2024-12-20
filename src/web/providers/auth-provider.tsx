import React, { createContext, useContext, useEffect, useCallback, useState, useRef } from 'react'; // v18.0.0
import axios from 'axios'; // v1.4.0
import { AuthState, LoginCredentials, RegisterData, AuthSchemas } from '../types/auth';
import { ApiError, ApiResponse, User } from '../types/api';

// Constants for configuration
const TOKEN_REFRESH_INTERVAL = 5 * 60 * 1000; // 5 minutes
const MAX_RETRY_ATTEMPTS = 3;
const INITIAL_AUTH_STATE: AuthState = {
  isAuthenticated: false,
  user: null,
  accessToken: null,
  loading: true,
  error: null,
};

// Type definition for the authentication context
interface AuthContextValue {
  state: AuthState;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
}

// Create the authentication context
const AuthContext = createContext<AuthContextValue | undefined>(undefined);

/**
 * Custom hook for managing authentication state and operations
 */
const useAuthProvider = (): AuthContextValue => {
  const [state, setState] = useState<AuthState>(INITIAL_AUTH_STATE);
  const refreshQueueRef = useRef<Promise<void> | null>(null);

  /**
   * Updates the authentication state with new values
   */
  const updateAuthState = useCallback((updates: Partial<AuthState>) => {
    setState(prev => ({ ...prev, ...updates }));
  }, []);

  /**
   * Handles token refresh with exponential backoff retry logic
   */
  const refreshToken = useCallback(async (retryAttempt = 0): Promise<void> => {
    // If there's already a refresh in progress, wait for it
    if (refreshQueueRef.current) {
      return refreshQueueRef.current;
    }

    const refreshOperation = async () => {
      try {
        const response = await axios.post<ApiResponse<{ accessToken: string }>>('/api/v1/auth/refresh', {}, {
          withCredentials: true // Required for sending refresh token cookie
        });

        updateAuthState({
          accessToken: response.data.data.accessToken,
          error: null
        });
      } catch (error) {
        if (retryAttempt < MAX_RETRY_ATTEMPTS) {
          const delay = Math.pow(2, retryAttempt) * 1000;
          await new Promise(resolve => setTimeout(resolve, delay));
          return refreshToken(retryAttempt + 1);
        }
        
        // If all retries fail, log out the user
        await logout();
      } finally {
        refreshQueueRef.current = null;
      }
    };

    refreshQueueRef.current = refreshOperation();
    return refreshQueueRef.current;
  }, []);

  /**
   * Handles user login with validation and error handling
   */
  const login = useCallback(async (credentials: LoginCredentials): Promise<void> => {
    try {
      updateAuthState({ loading: true, error: null });

      // Validate credentials
      AuthSchemas.loginSchema.parse(credentials);

      const response = await axios.post<ApiResponse<{ user: User; accessToken: string }>>('/api/v1/auth/login', credentials);

      updateAuthState({
        isAuthenticated: true,
        user: response.data.data.user,
        accessToken: response.data.data.accessToken,
        loading: false,
        error: null
      });
    } catch (error) {
      const apiError = error as ApiError;
      updateAuthState({
        isAuthenticated: false,
        user: null,
        accessToken: null,
        loading: false,
        error: 'invalid'
      });
      throw apiError;
    }
  }, []);

  /**
   * Handles user registration with validation and error handling
   */
  const register = useCallback(async (data: RegisterData): Promise<void> => {
    try {
      updateAuthState({ loading: true, error: null });

      // Validate registration data
      AuthSchemas.registerSchema.parse(data);

      const response = await axios.post<ApiResponse<{ user: User; accessToken: string }>>('/api/v1/auth/register', data);

      updateAuthState({
        isAuthenticated: true,
        user: response.data.data.user,
        accessToken: response.data.data.accessToken,
        loading: false,
        error: null
      });
    } catch (error) {
      const apiError = error as ApiError;
      updateAuthState({
        isAuthenticated: false,
        user: null,
        accessToken: null,
        loading: false,
        error: 'invalid'
      });
      throw apiError;
    }
  }, []);

  /**
   * Handles user logout with cleanup
   */
  const logout = useCallback(async (): Promise<void> => {
    try {
      if (state.isAuthenticated) {
        await axios.post('/api/v1/auth/logout', {}, {
          withCredentials: true
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      updateAuthState({
        isAuthenticated: false,
        user: null,
        accessToken: null,
        loading: false,
        error: null
      });
    }
  }, [state.isAuthenticated]);

  // Set up automatic token refresh
  useEffect(() => {
    let refreshInterval: NodeJS.Timeout;

    if (state.isAuthenticated && state.accessToken) {
      // Initial refresh
      refreshToken();

      // Set up periodic refresh
      refreshInterval = setInterval(refreshToken, TOKEN_REFRESH_INTERVAL);
    }

    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    };
  }, [state.isAuthenticated, state.accessToken, refreshToken]);

  return {
    state,
    login,
    register,
    logout,
    refreshToken
  };
};

/**
 * Authentication Provider component that wraps the application
 */
export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const auth = useAuthProvider();

  return (
    <AuthContext.Provider value={auth}>
      {children}
    </AuthContext.Provider>
  );
};

/**
 * Custom hook for accessing authentication context
 * @throws {Error} If used outside of AuthProvider
 */
export const useAuth = (): AuthContextValue => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthProvider;