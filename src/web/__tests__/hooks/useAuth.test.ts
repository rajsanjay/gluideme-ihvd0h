import { renderHook, act } from '@testing-library/react-hooks'; // v8.0.1
import { describe, it, expect, jest, beforeEach, afterEach } from '@jest/globals'; // v29.0.0
import { setupServer } from 'msw/node'; // v1.2.1
import { rest } from 'msw'; // v1.2.1
import { useAuth } from '../../hooks/useAuth';
import { AuthProvider } from '../../providers/auth-provider';
import type { AuthState, LoginCredentials, RegisterData } from '../../types/auth';
import type { User } from '../../types/api';

// Mock credentials and test data
const mockLoginCredentials: LoginCredentials = {
  email: 'test@example.com',
  password: 'Password123!',
  deviceId: 'test-device-001'
};

const mockRegisterData: RegisterData = {
  email: 'test@example.com',
  password: 'Password123!',
  role: 'student',
  institutionId: null,
  deviceId: 'test-device-001'
};

const mockUser: User = {
  id: '123e4567-e89b-12d3-a456-426614174000',
  email: 'test@example.com',
  role: 'student',
  institutionId: null,
  preferences: {},
  lastLogin: '2023-01-01T00:00:00Z'
};

const mockTokens = {
  accessToken: 'mock.jwt.token',
  refreshToken: 'mock.refresh.token',
  expiresIn: 900
};

// MSW server setup for API mocking
const server = setupServer(
  // Login endpoint mock
  rest.post('/api/v1/auth/login', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        data: {
          user: mockUser,
          accessToken: mockTokens.accessToken
        },
        status: 200,
        message: null
      })
    );
  }),

  // Register endpoint mock
  rest.post('/api/v1/auth/register', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        data: {
          user: mockUser,
          accessToken: mockTokens.accessToken
        },
        status: 200,
        message: null
      })
    );
  }),

  // Refresh token endpoint mock
  rest.post('/api/v1/auth/refresh', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        data: {
          accessToken: 'new.jwt.token'
        },
        status: 200,
        message: null
      })
    );
  }),

  // Logout endpoint mock
  rest.post('/api/v1/auth/logout', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        data: null,
        status: 200,
        message: 'Logged out successfully'
      })
    );
  })
);

// Test setup and cleanup
beforeAll(() => server.listen());
afterEach(() => {
  server.resetHandlers();
  localStorage.clear();
  sessionStorage.clear();
  jest.clearAllMocks();
});
afterAll(() => server.close());

// Mock crypto.subtle for device ID generation
const mockDigest = jest.fn().mockResolvedValue(new Uint8Array([1, 2, 3, 4]));
Object.defineProperty(global, 'crypto', {
  value: {
    subtle: {
      digest: mockDigest
    }
  }
});

// Helper function to render the hook with provider
const renderAuthHook = () => {
  return renderHook(() => useAuth(), {
    wrapper: ({ children }) => (
      <AuthProvider>{children}</AuthProvider>
    )
  });
};

describe('useAuth Hook', () => {
  describe('Initial State', () => {
    it('should start with unauthenticated state', () => {
      const { result } = renderAuthHook();
      
      expect(result.current.state).toEqual({
        isAuthenticated: false,
        user: null,
        accessToken: null,
        loading: true,
        error: null
      });
    });
  });

  describe('Login Flow', () => {
    it('should handle successful login', async () => {
      const { result } = renderAuthHook();

      await act(async () => {
        await result.current.login(mockLoginCredentials);
      });

      expect(result.current.state).toEqual({
        isAuthenticated: true,
        user: mockUser,
        accessToken: mockTokens.accessToken,
        loading: false,
        error: null
      });
    });

    it('should handle login failure', async () => {
      server.use(
        rest.post('/api/v1/auth/login', (req, res, ctx) => {
          return res(
            ctx.status(401),
            ctx.json({
              code: 'UNAUTHORIZED',
              message: 'Invalid credentials',
              errors: []
            })
          );
        })
      );

      const { result } = renderAuthHook();

      await act(async () => {
        try {
          await result.current.login(mockLoginCredentials);
        } catch (error) {
          expect(error).toBeDefined();
        }
      });

      expect(result.current.state.error).toBe('invalid');
      expect(result.current.state.isAuthenticated).toBe(false);
    });

    it('should prevent concurrent login attempts', async () => {
      const { result } = renderAuthHook();
      
      const loginPromise1 = result.current.login(mockLoginCredentials);
      const loginPromise2 = result.current.login(mockLoginCredentials);

      await act(async () => {
        await Promise.all([loginPromise1, loginPromise2]);
      });

      // Should only process one login attempt
      expect(mockDigest).toHaveBeenCalledTimes(1);
    });
  });

  describe('Token Management', () => {
    it('should handle token refresh', async () => {
      const { result } = renderAuthHook();

      // Login first
      await act(async () => {
        await result.current.login(mockLoginCredentials);
      });

      // Trigger token refresh
      await act(async () => {
        await result.current.refreshToken();
      });

      expect(result.current.state.accessToken).toBe('new.jwt.token');
    });

    it('should handle token refresh failure', async () => {
      server.use(
        rest.post('/api/v1/auth/refresh', (req, res, ctx) => {
          return res(ctx.status(401));
        })
      );

      const { result } = renderAuthHook();

      await act(async () => {
        await result.current.login(mockLoginCredentials);
        await result.current.refreshToken();
      });

      expect(result.current.state.isAuthenticated).toBe(false);
      expect(result.current.state.accessToken).toBeNull();
    });
  });

  describe('Permission Checking', () => {
    it('should correctly check user permissions', async () => {
      const { result } = renderAuthHook();

      await act(async () => {
        await result.current.login(mockLoginCredentials);
      });

      expect(result.current.checkPermission('view_requirements')).toBe(true);
      expect(result.current.checkPermission('manage_institution')).toBe(false);
    });

    it('should handle admin permissions correctly', async () => {
      server.use(
        rest.post('/api/v1/auth/login', (req, res, ctx) => {
          return res(
            ctx.status(200),
            ctx.json({
              data: {
                user: { ...mockUser, role: 'admin' },
                accessToken: mockTokens.accessToken
              }
            })
          );
        })
      );

      const { result } = renderAuthHook();

      await act(async () => {
        await result.current.login(mockLoginCredentials);
      });

      expect(result.current.checkPermission('any_permission')).toBe(true);
    });
  });

  describe('Logout Flow', () => {
    it('should handle successful logout', async () => {
      const { result } = renderAuthHook();

      // Login first
      await act(async () => {
        await result.current.login(mockLoginCredentials);
      });

      // Then logout
      await act(async () => {
        await result.current.logout();
      });

      expect(result.current.state).toEqual({
        isAuthenticated: false,
        user: null,
        accessToken: null,
        loading: false,
        error: null
      });

      expect(localStorage.getItem('lastLogin')).toBeNull();
      expect(Object.keys(sessionStorage)).toHaveLength(0);
    });

    it('should handle logout failure gracefully', async () => {
      server.use(
        rest.post('/api/v1/auth/logout', (req, res, ctx) => {
          return res(ctx.status(500));
        })
      );

      const { result } = renderAuthHook();

      await act(async () => {
        await result.current.login(mockLoginCredentials);
        await result.current.logout();
      });

      // Should still clear local state even if API fails
      expect(result.current.state.isAuthenticated).toBe(false);
      expect(result.current.state.user).toBeNull();
    });
  });

  describe('Registration Flow', () => {
    it('should handle successful registration', async () => {
      const { result } = renderAuthHook();

      await act(async () => {
        await result.current.register(mockRegisterData);
      });

      expect(result.current.state).toEqual({
        isAuthenticated: true,
        user: mockUser,
        accessToken: mockTokens.accessToken,
        loading: false,
        error: null
      });
    });

    it('should validate institution ID for institution-specific roles', async () => {
      const { result } = renderAuthHook();

      const invalidRegisterData = {
        ...mockRegisterData,
        role: 'institution_admin',
        institutionId: null
      };

      await act(async () => {
        try {
          await result.current.register(invalidRegisterData);
          fail('Should have thrown an error');
        } catch (error) {
          expect(error.message).toBe('Institution ID is required for this role');
        }
      });
    });
  });
});