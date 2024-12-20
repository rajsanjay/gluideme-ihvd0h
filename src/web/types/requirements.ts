// @ts-check
import { z } from 'zod'; // v3.21.0 - Runtime type validation
import type { Identifiable, Timestamps } from './common';

/**
 * Possible status values for transfer requirements
 */
export type RequirementStatus = 'draft' | 'published' | 'archived' | 'deprecated';

/**
 * Types of transfer requirements
 */
export type RequirementType = 'major' | 'general' | 'prerequisite' | 'elective';

/**
 * Severity levels for validation messages
 */
export type ValidationSeverity = 'error' | 'warning' | 'info';

/**
 * Course equivalency definition
 */
export interface CourseEquivalency {
  sourceCode: string;
  targetCode: string;
  credits: number;
  conditions?: string[];
  expirationDate?: string;
}

/**
 * Requirement rule structure
 */
export interface RequirementRule {
  id: string;
  type: string;
  criteria: Record<string, unknown>;
  minCredits?: number;
  maxCredits?: number;
  required: boolean;
  alternatives?: string[];
}

/**
 * Complete rules structure for a requirement
 */
export interface RequirementRules {
  courses: CourseEquivalency[];
  rules: RequirementRule[];
  totalCredits: number;
  minimumGPA?: number;
  additionalCriteria?: Record<string, unknown>;
}

/**
 * Version change tracking
 */
export interface VersionChange {
  field: string;
  oldValue: unknown;
  newValue: unknown;
  reason: string;
}

/**
 * Version information for requirements
 */
export interface RequirementVersion extends Timestamps {
  versionNumber: number;
  changes: VersionChange[];
  publishedBy: string;
  publishedAt: string;
}

/**
 * Audit comment structure
 */
export interface AuditComment {
  id: string;
  userId: string;
  comment: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

/**
 * Audit entry for tracking changes
 */
export interface AuditEntry extends Timestamps {
  userId: string;
  action: string;
  details: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

/**
 * Audit tracking for requirements
 */
export interface RequirementAudit {
  createdBy: string;
  lastModifiedBy: string;
  changeHistory: AuditEntry[];
  comments: AuditComment[];
}

/**
 * Workflow management for requirements
 */
export interface RequirementWorkflow {
  currentStage: string;
  approvers: string[];
  approvalStatus: Record<string, boolean>;
  dueDate: string | null;
}

/**
 * Validation error details
 */
export interface ValidationError {
  code: string;
  message: string;
  field?: string;
  severity: ValidationSeverity;
  details?: Record<string, unknown>;
}

/**
 * Validation warning details
 */
export interface ValidationWarning {
  code: string;
  message: string;
  field?: string;
  details?: Record<string, unknown>;
}

/**
 * Validation metadata
 */
export interface ValidationMetadata {
  validationRules: string[];
  context?: Record<string, unknown>;
  timestamp: string;
}

/**
 * Validation result structure
 */
export interface RequirementValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
  details: Record<string, unknown>;
  validationDate: string;
  validatedBy: string;
  metadata: ValidationMetadata;
}

/**
 * Core transfer requirement interface
 */
export interface TransferRequirement extends Identifiable, Timestamps {
  sourceInstitutionId: string;
  targetInstitutionId: string;
  majorCode: string;
  title: string;
  description: string;
  type: RequirementType;
  rules: RequirementRules;
  metadata: Record<string, any>;
  status: RequirementStatus;
  effectiveDate: string;
  expirationDate: string | null;
  version: RequirementVersion;
  audit: RequirementAudit;
  workflow: RequirementWorkflow;
}

/**
 * Zod schema for runtime validation of transfer requirements
 */
export const transferRequirementSchema = z.object({
  id: z.string().uuid(),
  sourceInstitutionId: z.string().uuid(),
  targetInstitutionId: z.string().uuid(),
  majorCode: z.string(),
  title: z.string().min(1),
  description: z.string(),
  type: z.enum(['major', 'general', 'prerequisite', 'elective']),
  rules: z.object({
    courses: z.array(z.object({
      sourceCode: z.string(),
      targetCode: z.string(),
      credits: z.number().positive(),
      conditions: z.array(z.string()).optional(),
      expirationDate: z.string().datetime().optional()
    })),
    rules: z.array(z.object({
      id: z.string().uuid(),
      type: z.string(),
      criteria: z.record(z.unknown()),
      minCredits: z.number().optional(),
      maxCredits: z.number().optional(),
      required: z.boolean(),
      alternatives: z.array(z.string()).optional()
    })),
    totalCredits: z.number().positive(),
    minimumGPA: z.number().min(0).max(4).optional(),
    additionalCriteria: z.record(z.unknown()).optional()
  }),
  metadata: z.record(z.any()),
  status: z.enum(['draft', 'published', 'archived', 'deprecated']),
  effectiveDate: z.string().datetime(),
  expirationDate: z.string().datetime().nullable(),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
  version: z.object({
    versionNumber: z.number().int().positive(),
    changes: z.array(z.object({
      field: z.string(),
      oldValue: z.unknown(),
      newValue: z.unknown(),
      reason: z.string()
    })),
    publishedBy: z.string().uuid(),
    publishedAt: z.string().datetime(),
    createdAt: z.string().datetime(),
    updatedAt: z.string().datetime()
  }),
  audit: z.object({
    createdBy: z.string().uuid(),
    lastModifiedBy: z.string().uuid(),
    changeHistory: z.array(z.object({
      userId: z.string().uuid(),
      action: z.string(),
      details: z.record(z.unknown()),
      metadata: z.record(z.unknown()).optional(),
      createdAt: z.string().datetime(),
      updatedAt: z.string().datetime()
    })),
    comments: z.array(z.object({
      id: z.string().uuid(),
      userId: z.string().uuid(),
      comment: z.string(),
      timestamp: z.string().datetime(),
      metadata: z.record(z.unknown()).optional()
    }))
  }),
  workflow: z.object({
    currentStage: z.string(),
    approvers: z.array(z.string().uuid()),
    approvalStatus: z.record(z.boolean()),
    dueDate: z.string().datetime().nullable()
  })
});