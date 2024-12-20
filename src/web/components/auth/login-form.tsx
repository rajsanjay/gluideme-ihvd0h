"use client";

import React, { memo, useCallback, useState } from 'react';
import { useForm } from 'react-hook-form'; // v7.45.0
import { zodResolver } from '@hookform/resolvers/zod'; // v3.0.0
import { z } from 'zod'; // v3.0.0
import { useAuth } from '../../hooks/useAuth';
import { FormField } from '../common/form-field';
import { Button } from '../common/button';

// Login form validation schema
const loginSchema = z.object({
  email: z
    .string()
    .email('Please enter a valid email address')
    .min(1, 'Email is required'),
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .max(100, 'Password is too long'),
  rememberMe: z.boolean().optional()
});

type LoginFormData = z.infer<typeof loginSchema>;

export interface LoginFormProps {
  onSuccess?: () => void;
  onError?: (error: AuthError) => void;
  className?: string;
  theme?: 'light' | 'dark';
  locale?: string;
}

/**
 * Enhanced login form component with comprehensive validation and accessibility
 * Implements secure authentication flow with real-time validation and user feedback
 */
export const LoginForm = memo<LoginFormProps>(({
  onSuccess,
  onError,
  className,
  theme = 'light',
  locale = 'en'
}) => {
  // Authentication state and login function
  const { login, state } = useAuth();
  const [showPassword, setShowPassword] = useState(false);

  // Form initialization with validation
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
    clearErrors
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
      rememberMe: false
    }
  });

  // Handle form submission
  const onSubmit = useCallback(async (data: LoginFormData) => {
    try {
      clearErrors();
      await login({
        email: data.email,
        password: data.password
      });
      onSuccess?.();
    } catch (error) {
      const authError = error as AuthError;
      if (authError.code === 'invalid_credentials') {
        setError('root', {
          type: 'manual',
          message: 'Invalid email or password'
        });
      } else {
        setError('root', {
          type: 'manual',
          message: 'An error occurred. Please try again.'
        });
      }
      onError?.(authError);
    }
  }, [login, clearErrors, setError, onSuccess, onError]);

  // Toggle password visibility
  const togglePasswordVisibility = useCallback(() => {
    setShowPassword(prev => !prev);
  }, []);

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className={className}
      noValidate
      aria-label="Login form"
    >
      {/* Email field */}
      <FormField
        id="email"
        name="email"
        type="email"
        label="Email address"
        error={errors.email?.message}
        required
        autoComplete="email"
        inputMode="email"
        aria-label="Email address"
        {...register('email')}
      />

      {/* Password field */}
      <div className="relative mt-4">
        <FormField
          id="password"
          name="password"
          type={showPassword ? 'text' : 'password'}
          label="Password"
          error={errors.password?.message}
          required
          autoComplete="current-password"
          aria-label="Password"
          {...register('password')}
        />
        <button
          type="button"
          onClick={togglePasswordVisibility}
          className="absolute right-3 top-9 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          aria-label={showPassword ? 'Hide password' : 'Show password'}
        >
          {showPassword ? '👁️' : '👁️‍🗨️'}
        </button>
      </div>

      {/* Remember me checkbox */}
      <div className="flex items-center mt-4">
        <input
          type="checkbox"
          id="rememberMe"
          className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500 dark:border-gray-600 dark:focus:ring-primary-400"
          {...register('rememberMe')}
        />
        <label
          htmlFor="rememberMe"
          className="ml-2 block text-sm text-gray-700 dark:text-gray-200"
        >
          Remember me
        </label>
      </div>

      {/* Error message */}
      {errors.root && (
        <div
          role="alert"
          className="mt-4 text-sm text-red-600 dark:text-red-400"
          aria-live="polite"
        >
          {errors.root.message}
        </div>
      )}

      {/* Submit button */}
      <Button
        type="submit"
        variant="primary"
        size="lg"
        className="w-full mt-6"
        isLoading={isSubmitting}
        isDisabled={isSubmitting}
        aria-label="Sign in"
      >
        {isSubmitting ? 'Signing in...' : 'Sign in'}
      </Button>

      {/* Loading state feedback */}
      {isSubmitting && (
        <div
          className="mt-4 text-sm text-gray-600 dark:text-gray-400 text-center"
          aria-live="polite"
        >
          Verifying your credentials...
        </div>
      )}
    </form>
  );
});

LoginForm.displayName = 'LoginForm';

export default LoginForm;