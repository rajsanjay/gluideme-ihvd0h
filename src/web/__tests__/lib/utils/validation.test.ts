import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals'; // v29.0.0
import { z } from 'zod'; // v3.21.0
import { render, screen, fireEvent } from '@testing-library/react'; // v13.0.0

import { 
  validateRequirementRules,
  validateFormData,
  formatValidationError,
  requirementSchema
} from '../../../lib/utils/validation';
import type { TransferRequirement } from '../../../types/requirements';

describe('validateRequirementRules', () => {
  const validRequirementRules = {
    courses: [
      {
        sourceCode: 'CS101',
        targetCode: 'COMP101',
        credits: 3,
        conditions: ['minimum grade C']
      }
    ],
    rules: [
      {
        id: '123e4567-e89b-12d3-a456-426614174000',
        type: 'prerequisite',
        criteria: { requiredGrade: 'C' },
        required: true
      }
    ],
    totalCredits: 60,
    minimumGPA: 2.0
  };

  it('should validate valid requirement rules successfully', async () => {
    const result = await validateRequirementRules(validRequirementRules);
    expect(result.isValid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  it('should validate GPA requirements with boundary values', async () => {
    // Test minimum GPA boundary
    const lowGPAResult = await validateRequirementRules({
      ...validRequirementRules,
      minimumGPA: -0.1
    });
    expect(lowGPAResult.isValid).toBe(false);
    expect(lowGPAResult.errors[0].code).toBe('INVALID_GPA');

    // Test maximum GPA boundary
    const highGPAResult = await validateRequirementRules({
      ...validRequirementRules,
      minimumGPA: 4.1
    });
    expect(highGPAResult.isValid).toBe(false);
    expect(highGPAResult.errors[0].code).toBe('INVALID_GPA');

    // Test valid GPA
    const validGPAResult = await validateRequirementRules({
      ...validRequirementRules,
      minimumGPA: 2.0
    });
    expect(validGPAResult.isValid).toBe(true);
  });

  it('should validate total credits requirements', async () => {
    // Test invalid total credits
    const invalidCreditsResult = await validateRequirementRules({
      ...validRequirementRules,
      totalCredits: 0
    });
    expect(invalidCreditsResult.isValid).toBe(false);
    expect(invalidCreditsResult.errors[0].code).toBe('INVALID_CREDITS');

    // Test valid total credits
    const validCreditsResult = await validateRequirementRules({
      ...validRequirementRules,
      totalCredits: 60
    });
    expect(validCreditsResult.isValid).toBe(true);
  });

  it('should detect duplicate course codes', async () => {
    const duplicateCourseRules = {
      ...validRequirementRules,
      courses: [
        {
          sourceCode: 'CS101',
          targetCode: 'COMP101',
          credits: 3
        },
        {
          sourceCode: 'CS101',
          targetCode: 'COMP102',
          credits: 3
        }
      ]
    };

    const result = await validateRequirementRules(duplicateCourseRules);
    expect(result.isValid).toBe(false);
    expect(result.errors[0].code).toBe('DUPLICATE_COURSE');
  });

  it('should validate course credits', async () => {
    const invalidCreditCourses = {
      ...validRequirementRules,
      courses: [
        {
          sourceCode: 'CS101',
          targetCode: 'COMP101',
          credits: 0
        }
      ]
    };

    const result = await validateRequirementRules(invalidCreditCourses);
    expect(result.isValid).toBe(false);
    expect(result.errors[0].code).toBe('INVALID_COURSE_CREDITS');
  });

  it('should detect circular dependencies in rules', async () => {
    const circularRules = {
      ...validRequirementRules,
      rules: [
        {
          id: 'rule1',
          type: 'prerequisite',
          criteria: {},
          required: true,
          alternatives: ['rule2']
        },
        {
          id: 'rule2',
          type: 'prerequisite',
          criteria: {},
          required: true,
          alternatives: ['rule1']
        }
      ]
    };

    const result = await validateRequirementRules(circularRules);
    expect(result.isValid).toBe(false);
    expect(result.errors[0].code).toBe('CIRCULAR_DEPENDENCY');
  });
});

describe('validateFormData', () => {
  const formSchema = z.object({
    email: z.string().email(),
    password: z.string().min(8),
    profile: z.object({
      name: z.string().min(1),
      preferences: z.object({
        notifications: z.boolean()
      })
    })
  });

  it('should validate valid form data successfully', () => {
    const validFormData = {
      email: 'test@example.com',
      password: 'password123',
      profile: {
        name: 'Test User',
        preferences: {
          notifications: true
        }
      }
    };

    const result = validateFormData(validFormData, formSchema);
    expect(result.success).toBe(true);
    expect(result.errors).toEqual({});
  });

  it('should validate email format correctly', () => {
    const invalidEmailData = {
      email: 'invalid-email',
      password: 'password123',
      profile: {
        name: 'Test User',
        preferences: {
          notifications: true
        }
      }
    };

    const result = validateFormData(invalidEmailData, formSchema);
    expect(result.success).toBe(false);
    expect(result.errors['email']).toBeDefined();
    expect(result.errors['email'].type).toBe('format');
  });

  it('should validate nested object fields', () => {
    const invalidNestedData = {
      email: 'test@example.com',
      password: 'password123',
      profile: {
        name: '',
        preferences: {
          notifications: true
        }
      }
    };

    const result = validateFormData(invalidNestedData, formSchema);
    expect(result.success).toBe(false);
    expect(result.errors['profile.name']).toBeDefined();
  });

  it('should include validation metadata', () => {
    const validFormData = {
      email: 'test@example.com',
      password: 'password123',
      profile: {
        name: 'Test User',
        preferences: {
          notifications: true
        }
      }
    };

    const result = validateFormData(validFormData, formSchema);
    expect(result.metadata).toBeDefined();
    expect(result.metadata.validationRules).toContain('form_validation');
    expect(result.metadata.timestamp).toBeDefined();
  });
});

describe('formatValidationError', () => {
  it('should format single validation error correctly', () => {
    const error = new z.ZodError([{
      code: 'invalid_type',
      expected: 'string',
      received: 'number',
      path: ['email'],
      message: 'Expected string, received number'
    }]);

    const formatted = formatValidationError(error);
    expect(formatted['email']).toBeDefined();
    expect(formatted['email'].type).toBe('format');
    expect(formatted['email'].severity).toBe('warning');
  });

  it('should format nested validation errors with correct paths', () => {
    const error = new z.ZodError([{
      code: 'invalid_type',
      expected: 'string',
      received: 'number',
      path: ['profile', 'name'],
      message: 'Expected string, received number'
    }]);

    const formatted = formatValidationError(error, { pathSeparator: '.' });
    expect(formatted['profile.name']).toBeDefined();
    expect(formatted['profile.name'].path).toEqual(['profile', 'name']);
  });

  it('should include metadata when specified', () => {
    const error = new z.ZodError([{
      code: 'invalid_type',
      expected: 'string',
      received: 'number',
      path: ['email'],
      message: 'Expected string, received number'
    }]);

    const formatted = formatValidationError(error, { includeMetadata: true });
    expect(formatted['email'].context).toBeDefined();
    expect(formatted['email'].context.code).toBe('invalid_type');
  });

  it('should determine correct severity levels', () => {
    const error = new z.ZodError([
      {
        code: 'required',
        path: ['required_field'],
        message: 'Required'
      },
      {
        code: 'invalid_type',
        path: ['format_field'],
        message: 'Invalid format'
      }
    ]);

    const formatted = formatValidationError(error);
    expect(formatted['required_field'].severity).toBe('error');
    expect(formatted['format_field'].severity).toBe('warning');
  });
});