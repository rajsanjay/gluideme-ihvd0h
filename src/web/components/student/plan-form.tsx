/**
 * @file PlanForm Component
 * @version 1.0.0
 * @description A comprehensive form component for creating and editing student transfer plans
 * with real-time validation, accessibility features, and progress tracking.
 */

import React, { memo, useCallback, useEffect, useState } from 'react';
import { z } from 'zod'; // v3.21.0
import { FormField } from '../common/form-field';
import { useForm } from '../../hooks/useForm';
import { useToast } from '../../hooks/useToast';
import { debounce } from 'lodash'; // v4.17.21
import type { TransferPlan } from '../../types/requirements';

// Plan form validation schema
const planFormSchema = z.object({
  targetInstitutionId: z.string().min(1, 'Target institution is required'),
  majorCode: z.string().min(1, 'Major is required'),
  academicYear: z.string().regex(/^\d{4}-\d{4}$/, 'Invalid academic year format'),
  courses: z.array(z.object({
    id: z.string(),
    code: z.string().min(1, 'Course code is required'),
    status: z.enum(['planned', 'completed', 'in_progress']),
    term: z.string().min(1, 'Term is required'),
    grade: z.string().optional()
  })).min(1, 'At least one course is required'),
  notes: z.string().max(500, 'Notes must be less than 500 characters').optional()
});

// Form props interface
export interface PlanFormProps {
  studentId: string;
  initialData?: TransferPlan;
  onSubmit: (data: z.infer<typeof planFormSchema>) => Promise<void>;
  onCancel: () => void;
  autoValidate?: boolean;
  validationConfig?: {
    validateOnBlur?: boolean;
    validateOnChange?: boolean;
    debounceMs?: number;
  };
  a11yConfig?: {
    announceValidation?: boolean;
    autoFocus?: boolean;
    preventSubmitOnEnter?: boolean;
  };
}

/**
 * PlanForm component for creating and editing transfer plans
 */
export const PlanForm = memo(({
  studentId,
  initialData,
  onSubmit,
  onCancel,
  autoValidate = true,
  validationConfig = {
    validateOnBlur: true,
    validateOnChange: false,
    debounceMs: 300
  },
  a11yConfig = {
    announceValidation: true,
    autoFocus: true,
    preventSubmitOnEnter: true
  }
}: PlanFormProps) => {
  // Initialize form state
  const [progress, setProgress] = useState(0);
  const toast = useToast();

  // Initialize form with validation
  const form = useForm(
    planFormSchema,
    initialData || {
      targetInstitutionId: '',
      majorCode: '',
      academicYear: '',
      courses: [],
      notes: ''
    },
    onSubmit,
    {
      validateOnBlur: validationConfig.validateOnBlur,
      validateOnChange: validationConfig.validateOnChange,
      toastOnError: true,
      preventSubmitOnEnter: a11yConfig.preventSubmitOnEnter
    }
  );

  // Debounced validation handler
  const debouncedValidate = useCallback(
    debounce(async () => {
      const isValid = await form.validate();
      if (a11yConfig.announceValidation) {
        const message = isValid ? 'Form is valid' : 'Form has errors';
        toast.show({ message, type: isValid ? 'success' : 'error' });
      }
    }, validationConfig.debounceMs),
    [form, a11yConfig.announceValidation]
  );

  // Update progress when form values change
  useEffect(() => {
    const calculateProgress = () => {
      const requiredFields = ['targetInstitutionId', 'majorCode', 'academicYear'];
      const completedFields = requiredFields.filter(field => form.values[field]);
      const courseProgress = form.values.courses.length > 0 ? 1 : 0;
      return ((completedFields.length + courseProgress) / (requiredFields.length + 1)) * 100;
    };

    setProgress(calculateProgress());
    if (autoValidate) {
      debouncedValidate();
    }
  }, [form.values, autoValidate, debouncedValidate]);

  return (
    <form
      onSubmit={form.handleSubmit}
      className="space-y-6"
      noValidate
      aria-label="Transfer Plan Form"
    >
      {/* Progress indicator */}
      <div
        role="progressbar"
        aria-valuenow={progress}
        aria-valuemin={0}
        aria-valuemax={100}
        className="w-full h-2 bg-gray-200 rounded-full overflow-hidden"
      >
        <div
          className="h-full bg-blue-500 transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Target Institution */}
      <FormField
        name="targetInstitutionId"
        label="Target Institution"
        value={form.values.targetInstitutionId}
        error={form.errors.targetInstitutionId}
        onChange={form.handleChange}
        onBlur={form.handleBlur}
        required
        autoFocus={a11yConfig.autoFocus}
        aria-describedby="institution-help"
      />

      {/* Major Selection */}
      <FormField
        name="majorCode"
        label="Major"
        value={form.values.majorCode}
        error={form.errors.majorCode}
        onChange={form.handleChange}
        onBlur={form.handleBlur}
        required
        aria-describedby="major-help"
      />

      {/* Academic Year */}
      <FormField
        name="academicYear"
        label="Academic Year"
        value={form.values.academicYear}
        error={form.errors.academicYear}
        onChange={form.handleChange}
        onBlur={form.handleBlur}
        required
        pattern="\d{4}-\d{4}"
        aria-describedby="year-help"
      />

      {/* Course List */}
      <div role="region" aria-label="Course List">
        {form.values.courses.map((course, index) => (
          <div key={course.id} className="space-y-4 p-4 border rounded-md">
            <FormField
              name={`courses.${index}.code`}
              label="Course Code"
              value={course.code}
              error={form.errors[`courses.${index}.code`]}
              onChange={(value) => form.setFieldValue(`courses.${index}.code`, value)}
              onBlur={() => form.setFieldTouched(`courses.${index}.code`, true)}
              required
            />
            <FormField
              name={`courses.${index}.status`}
              label="Status"
              value={course.status}
              error={form.errors[`courses.${index}.status`]}
              onChange={(value) => form.setFieldValue(`courses.${index}.status`, value)}
              onBlur={() => form.setFieldTouched(`courses.${index}.status`, true)}
              required
            />
            <FormField
              name={`courses.${index}.term`}
              label="Term"
              value={course.term}
              error={form.errors[`courses.${index}.term`]}
              onChange={(value) => form.setFieldValue(`courses.${index}.term`, value)}
              onBlur={() => form.setFieldTouched(`courses.${index}.term`, true)}
              required
            />
            {course.status === 'completed' && (
              <FormField
                name={`courses.${index}.grade`}
                label="Grade"
                value={course.grade || ''}
                error={form.errors[`courses.${index}.grade`]}
                onChange={(value) => form.setFieldValue(`courses.${index}.grade`, value)}
                onBlur={() => form.setFieldTouched(`courses.${index}.grade`, true)}
              />
            )}
          </div>
        ))}
        <button
          type="button"
          onClick={() => form.setFieldValue('courses', [
            ...form.values.courses,
            { id: crypto.randomUUID(), code: '', status: 'planned', term: '' }
          ])}
          className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          aria-label="Add Course"
        >
          Add Course
        </button>
      </div>

      {/* Notes */}
      <FormField
        name="notes"
        label="Notes"
        value={form.values.notes || ''}
        error={form.errors.notes}
        onChange={form.handleChange}
        onBlur={form.handleBlur}
        aria-describedby="notes-help"
      />

      {/* Form Actions */}
      <div className="flex justify-end space-x-4">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 border rounded hover:bg-gray-100"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={form.isSubmitting || !form.isValid}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
        >
          {form.isSubmitting ? 'Saving...' : 'Save Plan'}
        </button>
      </div>
    </form>
  );
});

PlanForm.displayName = 'PlanForm';

export default PlanForm;