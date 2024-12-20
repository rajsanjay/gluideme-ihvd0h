import { useContext, useCallback, useMemo } from 'react'; // v18.0.0
import { AuthContext } from '../providers/auth-provider';
import { AuthState, LoginCredentials, RegisterData } from '../types/auth';

/**
 * Custom hook providing secure access to authentication state and functionality
 * Implements JWT-based authentication with automatic token refresh and RBAC
 * 
 * @throws {Error} If used outside of AuthProvider context
 * @returns {Object} Authentication context value with state and functions
 */
export const useAuth = () => {
  // Get auth context and validate its existence
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  const { state, login, register, logout, refreshToken } = context;

  /**
   * Checks if the current user has a specific permission based on their role
   * Implements role-based access control according to the authorization matrix
   * 
   * @param {string} permission - The permission to check
   * @returns {boolean} Whether the user has the requested permission
   */
  const checkPermission = useCallback((permission: string): boolean => {
    if (!state.user || !state.isAuthenticated) {
      return false;
    }

    // Role-based permission mapping
    const rolePermissions: Record<string, string[]> = {
      admin: ['*'], // Admin has all permissions
      institution_admin: [
        'manage_requirements',
        'view_student_data',
        'generate_reports',
        'manage_institution'
      ],
      counselor: [
        'view_requirements',
        'view_student_data',
        'edit_student_plans'
      ],
      student: [
        'view_requirements',
        'view_own_data',
        'manage_own_plan'
      ],
      guest: [
        'view_public_requirements'
      ]
    };

    const userPermissions = rolePermissions[state.user.role] || [];
    
    return userPermissions.includes('*') || userPermissions.includes(permission);
  }, [state.user, state.isAuthenticated]);

  /**
   * Enhanced login function with additional security checks
   * 
   * @param {LoginCredentials} credentials - User login credentials
   * @returns {Promise<void>}
   */
  const secureLogin = useCallback(async (credentials: LoginCredentials): Promise<void> => {
    try {
      // Add device fingerprinting for enhanced security
      const deviceId = await generateDeviceId();
      await login({ ...credentials, deviceId });
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  }, [login]);

  /**
   * Enhanced registration function with role validation
   * 
   * @param {RegisterData} data - User registration data
   * @returns {Promise<void>}
   */
  const secureRegister = useCallback(async (data: RegisterData): Promise<void> => {
    try {
      // Add device fingerprinting for enhanced security
      const deviceId = await generateDeviceId();
      
      // Validate institution ID for institution-specific roles
      if (['institution_admin', 'counselor'].includes(data.role) && !data.institutionId) {
        throw new Error('Institution ID is required for this role');
      }

      await register({ ...data, deviceId });
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    }
  }, [register]);

  /**
   * Secure logout with cleanup
   * 
   * @returns {Promise<void>}
   */
  const secureLogout = useCallback(async (): Promise<void> => {
    try {
      await logout();
      // Clear any sensitive data from local storage
      localStorage.removeItem('lastLogin');
      sessionStorage.clear();
    } catch (error) {
      console.error('Logout failed:', error);
      throw error;
    }
  }, [logout]);

  /**
   * Generate a unique device identifier for security tracking
   * 
   * @returns {Promise<string>} Unique device identifier
   */
  const generateDeviceId = async (): Promise<string> => {
    const userAgent = navigator.userAgent;
    const screenResolution = `${window.screen.width}x${window.screen.height}`;
    const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    
    // Create a unique device fingerprint
    const fingerprint = await crypto.subtle.digest(
      'SHA-256',
      new TextEncoder().encode(`${userAgent}${screenResolution}${timeZone}`)
    );
    
    return Array.from(new Uint8Array(fingerprint))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');
  };

  // Memoize the return value to prevent unnecessary rerenders
  return useMemo(() => ({
    // Authentication state
    state,
    isAuthenticated: state.isAuthenticated,
    user: state.user,
    loading: state.loading,
    error: state.error,
    
    // Enhanced authentication functions
    login: secureLogin,
    register: secureRegister,
    logout: secureLogout,
    refreshToken,
    
    // Authorization functions
    checkPermission,
    
    // Helper functions
    isAdmin: state.user?.role === 'admin',
    isInstitutionAdmin: state.user?.role === 'institution_admin',
    isCounselor: state.user?.role === 'counselor',
    isStudent: state.user?.role === 'student',
    
    // Token management
    hasValidToken: Boolean(state.accessToken),
    
  }), [
    state,
    secureLogin,
    secureRegister,
    secureLogout,
    refreshToken,
    checkPermission
  ]);
};

export type UseAuthReturn = ReturnType<typeof useAuth>;