import { z } from 'zod'; // v3.21.0 - Runtime type validation
import type { 
  TransferRequirement, 
  RequirementValidationResult,
  ValidationError,
  ValidationMetadata,
  RequirementRules 
} from '../../types/requirements';

/**
 * Validation error types for categorizing validation failures
 */
export type ValidationErrorType = 'required' | 'format' | 'range' | 'custom' | 'nested' | 'dependency';

/**
 * Validation severity levels for error prioritization
 */
export type ValidationSeverity = 'error' | 'warning' | 'info';

/**
 * Options for customizing validation behavior
 */
interface ValidationOptions {
  abortEarly?: boolean;
  context?: Record<string, unknown>;
  customMessages?: Record<string, string>;
}

/**
 * Enhanced error information with metadata
 */
interface ValidationErrorInfo {
  message: string;
  type: ValidationErrorType;
  severity: ValidationSeverity;
  field: string;
  context?: Record<string, unknown>;
  path?: string[];
}

/**
 * Comprehensive validation result with metadata
 */
export interface ValidationResult {
  success: boolean;
  errors: Record<string, ValidationErrorInfo>;
  metadata: ValidationMetadata;
}

/**
 * Options for error message formatting
 */
interface ErrorFormatOptions {
  includeMetadata?: boolean;
  localize?: boolean;
  pathSeparator?: string;
}

/**
 * Enhanced requirement schema with comprehensive validation rules
 */
export const requirementSchema = z.object({
  rules: z.object({
    courses: z.array(z.object({
      sourceCode: z.string().min(1),
      targetCode: z.string().min(1),
      credits: z.number().positive(),
      conditions: z.array(z.string()).optional(),
      expirationDate: z.string().datetime().optional()
    })),
    totalCredits: z.number().positive(),
    minimumGPA: z.number().min(0).max(4).optional(),
    rules: z.array(z.object({
      id: z.string().uuid(),
      type: z.string(),
      criteria: z.record(z.unknown()),
      required: z.boolean(),
      alternatives: z.array(z.string()).optional()
    }))
  }),
  metadata: z.record(z.unknown())
});

/**
 * Validates requirement rules with enhanced validation logic
 * @param rules The requirement rules to validate
 * @returns Promise resolving to validation result
 */
export async function validateRequirementRules(
  rules: RequirementRules
): Promise<RequirementValidationResult> {
  const errors: ValidationError[] = [];
  const metadata: ValidationMetadata = {
    validationRules: [],
    timestamp: new Date().toISOString()
  };

  try {
    // Parse rules using Zod schema
    await requirementSchema.parseAsync({ rules });
    
    // Validate minimum GPA if specified
    if (rules.minimumGPA !== undefined) {
      if (rules.minimumGPA < 0 || rules.minimumGPA > 4.0) {
        errors.push({
          code: 'INVALID_GPA',
          message: 'GPA must be between 0.0 and 4.0',
          severity: 'error',
          field: 'minimumGPA'
        });
      }
      metadata.validationRules.push('gpa_range_check');
    }

    // Validate total credits
    if (rules.totalCredits <= 0) {
      errors.push({
        code: 'INVALID_CREDITS',
        message: 'Total credits must be greater than 0',
        severity: 'error',
        field: 'totalCredits'
      });
    }
    metadata.validationRules.push('credit_validation');

    // Validate course requirements
    const courseMap = new Map<string, boolean>();
    for (const course of rules.courses) {
      // Check for duplicate course codes
      if (courseMap.has(course.sourceCode)) {
        errors.push({
          code: 'DUPLICATE_COURSE',
          message: `Duplicate source course code: ${course.sourceCode}`,
          severity: 'error',
          field: 'courses'
        });
      }
      courseMap.set(course.sourceCode, true);

      // Validate course credits
      if (course.credits <= 0) {
        errors.push({
          code: 'INVALID_COURSE_CREDITS',
          message: `Invalid credits for course ${course.sourceCode}`,
          severity: 'error',
          field: 'courses'
        });
      }
    }
    metadata.validationRules.push('course_validation');

    // Check for circular prerequisites in rules
    const visited = new Set<string>();
    const recursionStack = new Set<string>();

    function checkCircularDependencies(ruleId: string): boolean {
      if (recursionStack.has(ruleId)) {
        return true;
      }
      if (visited.has(ruleId)) {
        return false;
      }

      visited.add(ruleId);
      recursionStack.add(ruleId);

      const rule = rules.rules.find(r => r.id === ruleId);
      if (rule?.alternatives) {
        for (const altId of rule.alternatives) {
          if (checkCircularDependencies(altId)) {
            return true;
          }
        }
      }

      recursionStack.delete(ruleId);
      return false;
    }

    for (const rule of rules.rules) {
      if (checkCircularDependencies(rule.id)) {
        errors.push({
          code: 'CIRCULAR_DEPENDENCY',
          message: `Circular dependency detected in rule ${rule.id}`,
          severity: 'error',
          field: 'rules'
        });
      }
    }
    metadata.validationRules.push('dependency_validation');

  } catch (error) {
    if (error instanceof z.ZodError) {
      errors.push(...error.errors.map(err => ({
        code: 'VALIDATION_ERROR',
        message: err.message,
        field: err.path.join('.'),
        severity: 'error'
      })));
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings: [],
    details: {},
    validationDate: new Date().toISOString(),
    validatedBy: 'system',
    metadata
  };
}

/**
 * Validates form data using provided schema with enhanced validation
 * @param data Form data to validate
 * @param schema Zod schema for validation
 * @param options Validation options
 * @returns Validation result with detailed error information
 */
export function validateFormData(
  data: Record<string, unknown>,
  schema: z.ZodSchema,
  options: ValidationOptions = {}
): ValidationResult {
  const errors: Record<string, ValidationErrorInfo> = {};
  const metadata: ValidationMetadata = {
    validationRules: ['form_validation'],
    context: options.context,
    timestamp: new Date().toISOString()
  };

  try {
    schema.parse(data);
    return {
      success: true,
      errors: {},
      metadata
    };
  } catch (error) {
    if (error instanceof z.ZodError) {
      const formattedErrors = formatValidationError(error, {
        includeMetadata: true,
        localize: true
      });
      return {
        success: false,
        errors: formattedErrors,
        metadata
      };
    }
    throw error;
  }
}

/**
 * Formats validation errors with enhanced error information
 * @param error Zod validation error
 * @param options Error formatting options
 * @returns Formatted error information
 */
export function formatValidationError(
  error: z.ZodError,
  options: ErrorFormatOptions = {}
): Record<string, ValidationErrorInfo> {
  const { pathSeparator = '.', includeMetadata = true } = options;
  const formattedErrors: Record<string, ValidationErrorInfo> = {};

  for (const err of error.errors) {
    const path = err.path.join(pathSeparator);
    const type = determineErrorType(err);
    const severity = determineSeverity(type);

    formattedErrors[path] = {
      message: err.message,
      type,
      severity,
      field: path,
      path: err.path,
      ...(includeMetadata && {
        context: {
          code: err.code,
          expected: err.expected,
          received: err.received
        }
      })
    };
  }

  return formattedErrors;
}

/**
 * Determines the type of validation error
 * @param error Zod validation error
 * @returns ValidationErrorType
 */
function determineErrorType(error: z.ZodIssue): ValidationErrorType {
  switch (error.code) {
    case 'invalid_type':
      return 'format';
    case 'required':
      return 'required';
    case 'too_small':
    case 'too_big':
      return 'range';
    case 'custom':
      return 'custom';
    case 'invalid_union':
      return 'nested';
    default:
      return 'custom';
  }
}

/**
 * Determines validation error severity
 * @param type Validation error type
 * @returns ValidationSeverity
 */
function determineSeverity(type: ValidationErrorType): ValidationSeverity {
  switch (type) {
    case 'required':
    case 'dependency':
      return 'error';
    case 'format':
    case 'range':
      return 'warning';
    default:
      return 'info';
  }
}