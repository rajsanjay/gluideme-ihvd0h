/**
 * @file RequirementForm Component
 * @version 1.0.0
 * @description A comprehensive form component for creating and editing transfer requirements
 * with real-time validation, accessibility support, and responsive design.
 */

import React, { useCallback, useEffect, useState } from 'react';
import { z } from 'zod'; // v3.21.0
import { useAutoAnimate } from '@formkit/auto-animate/react'; // v1.0.0
import { useMediaQuery } from '@mantine/hooks'; // v6.0.0
import { useForm } from '../../hooks/useForm';
import { FormField } from '../common/form-field';
import { useToast } from '../../hooks/useToast';
import type { TransferRequirement, RequirementType, RequirementStatus } from '../../types/requirements';

// Validation schema for transfer requirements
const requirementFormSchema = z.object({
  sourceInstitutionId: z.string().uuid('Invalid source institution'),
  targetInstitutionId: z.string().uuid('Invalid target institution'),
  majorCode: z.string().min(1, 'Major code is required'),
  title: z.string().min(1, 'Title is required').max(200, 'Title is too long'),
  description: z.string().min(1, 'Description is required'),
  type: z.enum(['major', 'general', 'prerequisite', 'elective'] as const),
  rules: z.object({
    courses: z.array(z.object({
      sourceCode: z.string().min(1, 'Source course code is required'),
      targetCode: z.string().min(1, 'Target course code is required'),
      credits: z.number().positive('Credits must be positive'),
      conditions: z.array(z.string()).optional(),
      expirationDate: z.string().datetime().optional()
    })),
    totalCredits: z.number().positive('Total credits must be positive'),
    minimumGPA: z.number().min(0).max(4).optional(),
    additionalCriteria: z.record(z.unknown()).optional()
  }),
  status: z.enum(['draft', 'published', 'archived', 'deprecated'] as const),
  effectiveDate: z.string().datetime(),
  metadata: z.record(z.unknown())
});

export interface RequirementFormProps {
  initialValues?: Partial<TransferRequirement>;
  onSubmit: (requirement: TransferRequirement) => Promise<void>;
  isEdit?: boolean;
  onCancel?: () => void;
  autoSave?: boolean;
}

export const RequirementForm: React.FC<RequirementFormProps> = ({
  initialValues,
  onSubmit,
  isEdit = false,
  onCancel,
  autoSave = false
}) => {
  // Initialize form with validation schema
  const form = useForm<TransferRequirement>(
    requirementFormSchema,
    {
      sourceInstitutionId: '',
      targetInstitutionId: '',
      majorCode: '',
      title: '',
      description: '',
      type: 'major',
      rules: {
        courses: [],
        totalCredits: 0,
        minimumGPA: undefined
      },
      status: 'draft',
      effectiveDate: new Date().toISOString(),
      metadata: {},
      ...initialValues
    },
    onSubmit,
    {
      validateOnBlur: true,
      validateOnChange: autoSave,
      toastOnError: true
    }
  );

  // Hooks for UI enhancements
  const toast = useToast();
  const [parent] = useAutoAnimate();
  const isMobile = useMediaQuery('(max-width: 768px)');

  // Auto-save functionality
  useEffect(() => {
    if (autoSave && form.isDirty) {
      const saveTimeout = setTimeout(() => {
        form.handleSubmit(new Event('submit') as any);
      }, 2000);

      return () => clearTimeout(saveTimeout);
    }
  }, [form.values, autoSave, form.isDirty]);

  // Course requirement management
  const handleAddCourse = useCallback(() => {
    form.setFieldValue('rules.courses', [
      ...form.values.rules.courses,
      {
        sourceCode: '',
        targetCode: '',
        credits: 0
      }
    ]);
  }, [form.values.rules.courses]);

  const handleRemoveCourse = useCallback((index: number) => {
    const newCourses = [...form.values.rules.courses];
    newCourses.splice(index, 1);
    form.setFieldValue('rules.courses', newCourses);
  }, [form.values.rules.courses]);

  return (
    <form
      onSubmit={form.handleSubmit}
      className="space-y-6"
      noValidate
      ref={parent}
    >
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <FormField
          name="title"
          label="Requirement Title"
          value={form.values.title}
          error={form.errors.title}
          onChange={(value) => form.setFieldValue('title', value)}
          onBlur={() => form.setFieldTouched('title', true)}
          required
          helpText="Enter a descriptive title for this requirement"
        />

        <FormField
          name="type"
          label="Requirement Type"
          value={form.values.type}
          error={form.errors.type}
          onChange={(value) => form.setFieldValue('type', value as RequirementType)}
          onBlur={() => form.setFieldTouched('type', true)}
          required
          type="text"
          inputMode="text"
        />
      </div>

      <FormField
        name="description"
        label="Description"
        value={form.values.description}
        error={form.errors.description}
        onChange={(value) => form.setFieldValue('description', value)}
        onBlur={() => form.setFieldTouched('description', true)}
        required
        helpText="Provide a detailed description of the requirement"
      />

      <div className="space-y-4">
        <h3 className="text-lg font-medium">Course Requirements</h3>
        <div ref={parent} className="space-y-4">
          {form.values.rules.courses.map((course, index) => (
            <div key={index} className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 border rounded">
              <FormField
                name={`rules.courses.${index}.sourceCode`}
                label="Source Course"
                value={course.sourceCode}
                error={form.errors[`rules.courses.${index}.sourceCode`]}
                onChange={(value) => {
                  const newCourses = [...form.values.rules.courses];
                  newCourses[index].sourceCode = value;
                  form.setFieldValue('rules.courses', newCourses);
                }}
                required
              />
              
              <FormField
                name={`rules.courses.${index}.targetCode`}
                label="Target Course"
                value={course.targetCode}
                error={form.errors[`rules.courses.${index}.targetCode`]}
                onChange={(value) => {
                  const newCourses = [...form.values.rules.courses];
                  newCourses[index].targetCode = value;
                  form.setFieldValue('rules.courses', newCourses);
                }}
                required
              />

              <div className="flex items-end">
                <button
                  type="button"
                  onClick={() => handleRemoveCourse(index)}
                  className="text-red-500 hover:text-red-700"
                  aria-label={`Remove course ${course.sourceCode || 'requirement'}`}
                >
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>

        <button
          type="button"
          onClick={handleAddCourse}
          className="text-blue-500 hover:text-blue-700"
        >
          Add Course Requirement
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <FormField
          name="rules.minimumGPA"
          label="Minimum GPA"
          value={String(form.values.rules.minimumGPA || '')}
          error={form.errors['rules.minimumGPA']}
          onChange={(value) => form.setFieldValue('rules.minimumGPA', parseFloat(value) || undefined)}
          type="number"
          inputMode="decimal"
          pattern="[0-4]\.?[0-9]*"
          helpText="Enter minimum GPA requirement (0-4.0)"
        />

        <FormField
          name="rules.totalCredits"
          label="Total Credits Required"
          value={String(form.values.rules.totalCredits)}
          error={form.errors['rules.totalCredits']}
          onChange={(value) => form.setFieldValue('rules.totalCredits', parseInt(value) || 0)}
          required
          type="number"
          inputMode="numeric"
          pattern="\d+"
        />
      </div>

      <div className="flex justify-end space-x-4">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-gray-600 hover:text-gray-800"
          >
            Cancel
          </button>
        )}
        
        <button
          type="submit"
          disabled={form.isSubmitting || !form.isValid}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
        >
          {form.isSubmitting ? 'Saving...' : isEdit ? 'Update Requirement' : 'Create Requirement'}
        </button>
      </div>
    </form>
  );
};

export default RequirementForm;