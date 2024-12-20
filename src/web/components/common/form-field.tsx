/**
 * @file FormField Component
 * @version 1.0.0
 * @description A reusable form field component providing consistent styling, validation,
 * error handling, and accessibility features across the application.
 *
 * @requires react ^18.2.0
 * @requires class-variance-authority ^0.7.0
 * @requires use-debounce ^9.0.0
 */

import React, { memo, useCallback, useEffect, useId, useState } from 'react';
import { cn } from 'class-variance-authority';
import { useDebounce } from 'use-debounce';
import { validateFormData } from '../../lib/utils/validation';
import { Tooltip } from './tooltip';

// Form field variants using class-variance-authority
export const formFieldVariants = cn({
  base: 'w-full rounded-md border transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2',
  variants: {
    intent: {
      primary: 'border-gray-300 focus:border-blue-500 dark:border-gray-600 dark:focus:border-blue-400',
      error: 'border-red-500 focus:border-red-500 dark:border-red-400 dark:focus:border-red-400',
      success: 'border-green-500 focus:border-green-500 dark:border-green-400 dark:focus:border-green-400',
      warning: 'border-yellow-500 focus:border-yellow-500 dark:border-yellow-400 dark:focus:border-yellow-400'
    },
    size: {
      sm: 'text-sm py-1 px-2',
      md: 'text-base py-2 px-3',
      lg: 'text-lg py-3 px-4'
    },
    state: {
      default: 'bg-white dark:bg-gray-800',
      disabled: 'bg-gray-100 cursor-not-allowed dark:bg-gray-700',
      readonly: 'bg-gray-50 dark:bg-gray-900'
    }
  },
  defaultVariants: {
    intent: 'primary',
    size: 'md',
    state: 'default'
  }
});

// Form field props interface
export interface FormFieldProps {
  id?: string;
  name: string;
  label: string;
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url';
  placeholder?: string;
  value: string;
  error?: string;
  helpText?: string;
  required?: boolean;
  disabled?: boolean;
  onChange: (value: string) => void;
  onBlur?: () => void;
  className?: string;
  validationRules?: Record<string, unknown>;
  ariaLabel?: string;
  ariaDescribedBy?: string;
  autoComplete?: boolean;
  inputMode?: 'none' | 'text' | 'decimal' | 'numeric' | 'tel' | 'search' | 'email' | 'url';
  pattern?: string;
}

/**
 * FormField component with comprehensive validation and accessibility features
 */
export const FormField = memo(({
  id: propId,
  name,
  label,
  type = 'text',
  placeholder,
  value,
  error,
  helpText,
  required = false,
  disabled = false,
  onChange,
  onBlur,
  className,
  validationRules,
  ariaLabel,
  ariaDescribedBy,
  autoComplete,
  inputMode,
  pattern
}: FormFieldProps) => {
  // Generate unique IDs for accessibility
  const uniqueId = useId();
  const id = propId || `field-${uniqueId}`;
  const errorId = `${id}-error`;
  const helpId = `${id}-help`;

  // State management
  const [isFocused, setIsFocused] = useState(false);
  const [isDirty, setIsDirty] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [debouncedValue] = useDebounce(value, 300);

  // Determine field variant based on state
  const fieldVariant = cn(
    formFieldVariants({
      intent: validationError || error ? 'error' : isFocused ? 'primary' : undefined,
      state: disabled ? 'disabled' : undefined,
      className
    })
  );

  // Handle real-time validation
  useEffect(() => {
    if (isDirty && validationRules) {
      const validate = async () => {
        try {
          const result = await validateFormData(
            { [name]: debouncedValue },
            validationRules
          );
          setValidationError(result.success ? null : Object.values(result.errors)[0]?.message);
        } catch (err) {
          console.error('Validation error:', err);
          setValidationError('Validation failed');
        }
      };
      validate();
    }
  }, [debouncedValue, isDirty, name, validationRules]);

  // Event handlers
  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setIsDirty(true);
    onChange(e.target.value);
  }, [onChange]);

  const handleBlur = useCallback(() => {
    setIsFocused(false);
    setIsDirty(true);
    onBlur?.();
  }, [onBlur]);

  const handleFocus = useCallback(() => {
    setIsFocused(true);
  }, []);

  // Compute ARIA attributes
  const ariaAttributes = {
    'aria-label': ariaLabel || label,
    'aria-invalid': Boolean(error || validationError),
    'aria-required': required,
    'aria-describedby': cn(
      helpText && helpId,
      (error || validationError) && errorId,
      ariaDescribedBy
    )
  };

  return (
    <div className="relative space-y-2">
      <label
        htmlFor={id}
        className={cn(
          'block text-sm font-medium',
          disabled && 'text-gray-500 dark:text-gray-400'
        )}
      >
        {label}
        {required && (
          <span className="ml-1 text-red-500 dark:text-red-400" aria-hidden="true">
            *
          </span>
        )}
      </label>

      <div className="relative">
        <input
          id={id}
          name={name}
          type={type}
          value={value}
          onChange={handleChange}
          onBlur={handleBlur}
          onFocus={handleFocus}
          disabled={disabled}
          placeholder={placeholder}
          className={fieldVariant}
          autoComplete={autoComplete ? 'on' : 'off'}
          inputMode={inputMode}
          pattern={pattern}
          {...ariaAttributes}
        />

        {(error || validationError || helpText) && (
          <Tooltip
            content={
              <div className="space-y-1">
                {(error || validationError) && (
                  <p id={errorId} className="text-red-500 dark:text-red-400">
                    {error || validationError}
                  </p>
                )}
                {helpText && (
                  <p id={helpId} className="text-gray-500 dark:text-gray-400">
                    {helpText}
                  </p>
                )}
              </div>
            }
            position="right"
          >
            <div
              className={cn(
                'absolute right-2 top-1/2 -translate-y-1/2',
                (error || validationError) ? 'text-red-500' : 'text-gray-400'
              )}
            >
              <span className="sr-only">
                {error || validationError ? 'Error' : 'Help'}
              </span>
              {error || validationError ? '!' : '?'}
            </div>
          </Tooltip>
        )}
      </div>
    </div>
  );
});

FormField.displayName = 'FormField';

export default FormField;