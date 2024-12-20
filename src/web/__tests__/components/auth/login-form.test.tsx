import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'; // v14.0.0
import userEvent from '@testing-library/user-event'; // v14.0.0
import { vi, describe, it, expect, beforeEach } from 'vitest'; // v0.34.0
import LoginForm from '../../../components/auth/login-form';
import { useAuth } from '../../../hooks/useAuth';
import type { AuthError } from '../../../types/auth';

// Mock useAuth hook
vi.mock('../../../hooks/useAuth', () => ({
  useAuth: vi.fn()
}));

// Test data constants
const VALID_EMAIL = 'test@example.com';
const VALID_PASSWORD = 'Password123!';
const INVALID_EMAIL = 'invalid-email';
const SHORT_PASSWORD = 'pass';

// Helper function to setup test environment
interface SetupOptions {
  mockLoginSuccess?: boolean;
  mockLoginError?: AuthError;
  onSuccess?: () => void;
  onError?: (error: AuthError) => void;
}

const setupTest = async (options: SetupOptions = {}) => {
  const {
    mockLoginSuccess = true,
    mockLoginError,
    onSuccess = vi.fn(),
    onError = vi.fn()
  } = options;

  // Mock auth hook implementation
  const mockLogin = vi.fn().mockImplementation(async () => {
    if (!mockLoginSuccess) {
      throw mockLoginError || { code: 'invalid_credentials' };
    }
  });

  (useAuth as jest.Mock).mockReturnValue({
    login: mockLogin,
    state: {
      loading: false,
      error: null
    }
  });

  // Create user event instance
  const user = userEvent.setup();

  // Render component
  const result = render(
    <LoginForm
      onSuccess={onSuccess}
      onError={onError}
      theme="light"
      locale="en"
    />
  );

  return {
    user,
    ...result,
    mockLogin,
    onSuccess,
    onError
  };
};

describe('LoginForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders all form elements with correct attributes', async () => {
      const { container } = await setupTest();

      // Check form accessibility
      const form = container.querySelector('form');
      expect(form).toHaveAttribute('aria-label', 'Login form');
      expect(form).toHaveAttribute('noValidate');

      // Check email field
      const emailInput = screen.getByLabelText(/email address/i);
      expect(emailInput).toHaveAttribute('type', 'email');
      expect(emailInput).toHaveAttribute('required');
      expect(emailInput).toHaveAttribute('autocomplete', 'email');
      expect(emailInput).toHaveAttribute('inputmode', 'email');

      // Check password field
      const passwordInput = screen.getByLabelText(/password/i);
      expect(passwordInput).toHaveAttribute('type', 'password');
      expect(passwordInput).toHaveAttribute('required');
      expect(passwordInput).toHaveAttribute('autocomplete', 'current-password');

      // Check remember me checkbox
      const rememberMe = screen.getByLabelText(/remember me/i);
      expect(rememberMe).toHaveAttribute('type', 'checkbox');

      // Check submit button
      const submitButton = screen.getByRole('button', { name: /sign in/i });
      expect(submitButton).toBeEnabled();
    });

    it('maintains accessibility requirements', async () => {
      const { container } = await setupTest();
      
      // Check ARIA labels and roles
      expect(container.querySelector('[aria-label="Login form"]')).toBeInTheDocument();
      expect(screen.getByLabelText(/email address/i)).toHaveAttribute('aria-required', 'true');
      expect(screen.getByLabelText(/password/i)).toHaveAttribute('aria-required', 'true');
      
      // Check focus management
      const emailInput = screen.getByLabelText(/email address/i);
      emailInput.focus();
      expect(emailInput).toHaveFocus();
    });
  });

  describe('Form Validation', () => {
    it('validates required fields on submission', async () => {
      const { user } = await setupTest();

      // Submit empty form
      const submitButton = screen.getByRole('button', { name: /sign in/i });
      await user.click(submitButton);

      // Check error messages
      expect(await screen.findByText(/email is required/i)).toBeInTheDocument();
      expect(await screen.findByText(/password must be at least 8 characters/i)).toBeInTheDocument();
    });

    it('validates email format', async () => {
      const { user } = await setupTest();

      // Enter invalid email
      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, INVALID_EMAIL);
      emailInput.blur();

      // Check error message
      expect(await screen.findByText(/please enter a valid email address/i)).toBeInTheDocument();
    });

    it('validates password requirements', async () => {
      const { user } = await setupTest();

      // Enter short password
      const passwordInput = screen.getByLabelText(/password/i);
      await user.type(passwordInput, SHORT_PASSWORD);
      passwordInput.blur();

      // Check error message
      expect(await screen.findByText(/password must be at least 8 characters/i)).toBeInTheDocument();
    });
  });

  describe('Authentication Flow', () => {
    it('handles successful login', async () => {
      const { user, mockLogin, onSuccess } = await setupTest({ mockLoginSuccess: true });

      // Fill form with valid data
      await user.type(screen.getByLabelText(/email address/i), VALID_EMAIL);
      await user.type(screen.getByLabelText(/password/i), VALID_PASSWORD);

      // Submit form
      await user.click(screen.getByRole('button', { name: /sign in/i }));

      // Verify login attempt
      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith({
          email: VALID_EMAIL,
          password: VALID_PASSWORD
        });
      });

      // Verify success callback
      expect(onSuccess).toHaveBeenCalled();
    });

    it('handles authentication failure', async () => {
      const mockError: AuthError = {
        code: 'invalid_credentials',
        message: 'Invalid email or password'
      };

      const { user, onError } = await setupTest({
        mockLoginSuccess: false,
        mockLoginError: mockError
      });

      // Fill and submit form
      await user.type(screen.getByLabelText(/email address/i), VALID_EMAIL);
      await user.type(screen.getByLabelText(/password/i), VALID_PASSWORD);
      await user.click(screen.getByRole('button', { name: /sign in/i }));

      // Verify error handling
      expect(await screen.findByText(/invalid email or password/i)).toBeInTheDocument();
      expect(onError).toHaveBeenCalledWith(mockError);
    });
  });

  describe('User Interaction States', () => {
    it('shows loading state during authentication', async () => {
      const { user } = await setupTest({
        mockLoginSuccess: true
      });

      // Fill and submit form
      await user.type(screen.getByLabelText(/email address/i), VALID_EMAIL);
      await user.type(screen.getByLabelText(/password/i), VALID_PASSWORD);
      await user.click(screen.getByRole('button', { name: /sign in/i }));

      // Verify loading state
      expect(screen.getByText(/signing in/i)).toBeInTheDocument();
      expect(screen.getByText(/verifying your credentials/i)).toBeInTheDocument();
    });

    it('handles password visibility toggle', async () => {
      const { user } = await setupTest();

      const passwordInput = screen.getByLabelText(/password/i);
      const toggleButton = screen.getByRole('button', { name: /show password/i });

      // Initial state - password hidden
      expect(passwordInput).toHaveAttribute('type', 'password');

      // Toggle password visibility
      await user.click(toggleButton);
      expect(passwordInput).toHaveAttribute('type', 'text');
      expect(toggleButton).toHaveAttribute('aria-label', 'Hide password');

      // Toggle back
      await user.click(toggleButton);
      expect(passwordInput).toHaveAttribute('type', 'password');
      expect(toggleButton).toHaveAttribute('aria-label', 'Show password');
    });
  });
});