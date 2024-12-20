/**
 * @file RegisterForm Component
 * @version 1.0.0
 * @description A comprehensive React form component for secure user registration
 * with role-based validation, accessibility features, and real-time error handling.
 */

import React, { useCallback, useMemo } from 'react';
import { z } from 'zod'; // v3.21.0
import classNames from 'classnames'; // v2.3.2
import { useForm } from '../../hooks/useForm';
import { useAuth } from '../../hooks/useAuth';
import { useToast } from '../../hooks/useToast';
import { FormField } from '../common/form-field';
import { Button } from '../common/button';
import type { UserRole } from '../../types/auth';

// Registration form data interface
interface RegisterFormData {
  email: string;
  password: string;
  confirmPassword: string;
  role: UserRole;
  institutionId: string | null;
  firstName: string;
  lastName: string;
}

// Component props interface
interface RegisterFormProps {
  onSuccess?: () => void;
  onError?: (error: Error) => void;
  className?: string;
  initialValues?: Partial<RegisterFormData>;
}

// Zod schema for form validation
const registerFormSchema = z.object({
  email: z.string()
    .email('Invalid email format')
    .min(1, 'Email is required'),
  password: z.string()
    .min(8, 'Password must be at least 8 characters')
    .regex(
      /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$/,
      'Password must include uppercase, lowercase, number and special character'
    ),
  confirmPassword: z.string()
    .min(1, 'Please confirm your password'),
  role: z.enum(['admin', 'institution_admin', 'counselor', 'student', 'guest'] as const),
  institutionId: z.string().nullable(),
  firstName: z.string()
    .min(1, 'First name is required')
    .max(50, 'First name is too long'),
  lastName: z.string()
    .min(1, 'Last name is required')
    .max(50, 'Last name is too long'),
}).refine(
  (data) => data.password === data.confirmPassword,
  {
    message: "Passwords don't match",
    path: ['confirmPassword']
  }
).refine(
  (data) => {
    if (['institution_admin', 'counselor'].includes(data.role) && !data.institutionId) {
      return false;
    }
    return true;
  },
  {
    message: 'Institution ID is required for this role',
    path: ['institutionId']
  }
);

/**
 * RegisterForm Component
 * 
 * A comprehensive registration form with role-based validation,
 * real-time error checking, and accessibility features.
 */
export const RegisterForm: React.FC<RegisterFormProps> = ({
  onSuccess,
  onError,
  className,
  initialValues
}) => {
  const { register, isLoading } = useAuth();
  const toast = useToast();

  // Default form values
  const defaultValues: RegisterFormData = {
    email: '',
    password: '',
    confirmPassword: '',
    role: 'student',
    institutionId: null,
    firstName: '',
    lastName: '',
    ...initialValues
  };

  // Initialize form with validation schema
  const form = useForm<RegisterFormData>(
    registerFormSchema,
    defaultValues,
    async (values) => {
      try {
        await register({
          email: values.email,
          password: values.password,
          role: values.role,
          institutionId: values.institutionId,
          firstName: values.firstName,
          lastName: values.lastName
        });
        
        toast.show({
          message: 'Registration successful!',
          type: 'success'
        });
        
        onSuccess?.();
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Registration failed';
        toast.show({
          message: errorMessage,
          type: 'error'
        });
        onError?.(error instanceof Error ? error : new Error(errorMessage));
      }
    },
    {
      validateOnBlur: true,
      validateOnChange: false
    }
  );

  // Handle role change with institution validation
  const handleRoleChange = useCallback((event: React.ChangeEvent<HTMLSelectElement>) => {
    const newRole = event.target.value as UserRole;
    form.setFieldValue('role', newRole);
    
    // Clear institution ID if switching to student/guest role
    if (!['institution_admin', 'counselor'].includes(newRole)) {
      form.setFieldValue('institutionId', null);
    }
  }, [form]);

  // Compute whether institution field should be shown
  const showInstitutionField = useMemo(() => {
    return ['institution_admin', 'counselor'].includes(form.values.role);
  }, [form.values.role]);

  return (
    <form
      onSubmit={form.handleSubmit}
      className={classNames('space-y-6', className)}
      noValidate
    >
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <FormField
          name="firstName"
          label="First Name"
          value={form.values.firstName}
          error={form.errors.firstName}
          onChange={(value) => form.setFieldValue('firstName', value)}
          onBlur={() => form.handleBlur({ target: { name: 'firstName' } } as any)}
          required
          autoComplete="given-name"
        />

        <FormField
          name="lastName"
          label="Last Name"
          value={form.values.lastName}
          error={form.errors.lastName}
          onChange={(value) => form.setFieldValue('lastName', value)}
          onBlur={() => form.handleBlur({ target: { name: 'lastName' } } as any)}
          required
          autoComplete="family-name"
        />
      </div>

      <FormField
        name="email"
        label="Email"
        type="email"
        value={form.values.email}
        error={form.errors.email}
        onChange={(value) => form.setFieldValue('email', value)}
        onBlur={() => form.handleBlur({ target: { name: 'email' } } as any)}
        required
        autoComplete="email"
      />

      <FormField
        name="password"
        label="Password"
        type="password"
        value={form.values.password}
        error={form.errors.password}
        onChange={(value) => form.setFieldValue('password', value)}
        onBlur={() => form.handleBlur({ target: { name: 'password' } } as any)}
        required
        autoComplete="new-password"
      />

      <FormField
        name="confirmPassword"
        label="Confirm Password"
        type="password"
        value={form.values.confirmPassword}
        error={form.errors.confirmPassword}
        onChange={(value) => form.setFieldValue('confirmPassword', value)}
        onBlur={() => form.handleBlur({ target: { name: 'confirmPassword' } } as any)}
        required
        autoComplete="new-password"
      />

      <div className="space-y-2">
        <label
          htmlFor="role"
          className="block text-sm font-medium text-gray-700 dark:text-gray-200"
        >
          Role
        </label>
        <select
          id="role"
          name="role"
          value={form.values.role}
          onChange={handleRoleChange}
          onBlur={() => form.handleBlur({ target: { name: 'role' } } as any)}
          className="block w-full rounded-md border border-gray-300 bg-white py-2 px-3 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-primary-500 dark:border-gray-600 dark:bg-gray-800"
          required
        >
          <option value="student">Student</option>
          <option value="counselor">Counselor</option>
          <option value="institution_admin">Institution Administrator</option>
          <option value="guest">Guest</option>
        </select>
      </div>

      {showInstitutionField && (
        <FormField
          name="institutionId"
          label="Institution ID"
          value={form.values.institutionId || ''}
          error={form.errors.institutionId}
          onChange={(value) => form.setFieldValue('institutionId', value)}
          onBlur={() => form.handleBlur({ target: { name: 'institutionId' } } as any)}
          required
        />
      )}

      <Button
        type="submit"
        variant="primary"
        size="lg"
        className="w-full"
        isLoading={isLoading}
        isDisabled={!form.isValid || isLoading}
      >
        Create Account
      </Button>
    </form>
  );
};

export default RegisterForm;