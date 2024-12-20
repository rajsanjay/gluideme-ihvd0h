// @ts-check
import { z } from 'zod'; // v3.21.0 - Runtime type validation
import type { Identifiable, Timestamps } from './common';
import type { TransferRequirement } from './requirements';

/**
 * Possible statuses for a transfer plan
 */
export type PlanStatus = 'draft' | 'submitted' | 'approved' | 'rejected';

/**
 * Status of a planned or completed course
 */
export type CourseStatus = 'planned' | 'in_progress' | 'completed' | 'failed';

/**
 * Overall progress status for requirements
 */
export type ProgressStatus = 'not_started' | 'in_progress' | 'completed';

/**
 * Student academic profile information
 */
export interface StudentProfile extends Identifiable, Timestamps {
  /** Associated user ID */
  userId: string;
  /** Current institution ID */
  sourceInstitutionId: string;
  /** Academic information */
  academicInfo: AcademicInfo;
  /** User preferences */
  preferences: Record<string, unknown>;
}

/**
 * Academic information for a student
 */
export interface AcademicInfo {
  /** Student's declared major code */
  majorCode: string;
  /** Current cumulative GPA */
  currentGPA: number;
  /** Total completed units */
  totalUnits: number;
  /** Current enrollment status (e.g., 'full_time', 'part_time') */
  enrollmentStatus: string;
  /** Expected graduation date */
  expectedGraduation: string;
}

/**
 * Transfer plan for a student
 */
export interface TransferPlan extends Identifiable, Timestamps {
  /** Associated student ID */
  studentId: string;
  /** Associated transfer requirement ID */
  requirementId: string;
  /** Target institution ID */
  targetInstitutionId: string;
  /** Current plan status */
  status: PlanStatus;
  /** Planned courses */
  courses: PlannedCourse[];
  /** Progress tracking */
  progress: TransferProgress;
  /** Additional notes */
  notes: string;
}

/**
 * Course within a transfer plan
 */
export interface PlannedCourse {
  /** Course ID */
  courseId: string;
  /** Current status */
  status: CourseStatus;
  /** Academic term (e.g., 'Fall 2023') */
  term: string;
  /** Achieved grade (if completed) */
  grade: string | null;
  /** Course units/credits */
  units: number;
}

/**
 * Progress tracking for transfer requirements
 */
export interface TransferProgress {
  /** Overall completion status */
  overallStatus: ProgressStatus;
  /** Total completed units */
  completedUnits: number;
  /** Total required units */
  requiredUnits: number;
  /** Current transfer GPA */
  currentGPA: number;
  /** Individual requirement progress */
  requirementProgress: RequirementProgress[];
}

/**
 * Progress tracking for individual requirements
 */
export interface RequirementProgress {
  /** Associated requirement ID */
  requirementId: string;
  /** Completion status */
  status: ProgressStatus;
  /** Number of completed items */
  completedItems: number;
  /** Total number of required items */
  totalItems: number;
  /** Additional progress details */
  details: Record<string, unknown>;
}

/**
 * Zod schema for runtime validation of student profile
 */
export const studentProfileSchema = z.object({
  id: z.string().uuid(),
  userId: z.string().uuid(),
  sourceInstitutionId: z.string().uuid(),
  academicInfo: z.object({
    majorCode: z.string(),
    currentGPA: z.number().min(0).max(4),
    totalUnits: z.number().nonnegative(),
    enrollmentStatus: z.string(),
    expectedGraduation: z.string().datetime()
  }),
  preferences: z.record(z.unknown()),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime()
});

/**
 * Zod schema for runtime validation of transfer plans
 */
export const transferPlanSchema = z.object({
  id: z.string().uuid(),
  studentId: z.string().uuid(),
  requirementId: z.string().uuid(),
  targetInstitutionId: z.string().uuid(),
  status: z.enum(['draft', 'submitted', 'approved', 'rejected']),
  courses: z.array(z.object({
    courseId: z.string().uuid(),
    status: z.enum(['planned', 'in_progress', 'completed', 'failed']),
    term: z.string(),
    grade: z.string().nullable(),
    units: z.number().positive()
  })),
  progress: z.object({
    overallStatus: z.enum(['not_started', 'in_progress', 'completed']),
    completedUnits: z.number().nonnegative(),
    requiredUnits: z.number().positive(),
    currentGPA: z.number().min(0).max(4),
    requirementProgress: z.array(z.object({
      requirementId: z.string().uuid(),
      status: z.enum(['not_started', 'in_progress', 'completed']),
      completedItems: z.number().nonnegative(),
      totalItems: z.number().positive(),
      details: z.record(z.unknown())
    }))
  }),
  notes: z.string(),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime()
});

/**
 * Type guard to check if a value is a valid PlanStatus
 */
export const isPlanStatus = (value: unknown): value is PlanStatus => {
  return ['draft', 'submitted', 'approved', 'rejected'].includes(value as string);
};

/**
 * Type guard to check if a value is a valid CourseStatus
 */
export const isCourseStatus = (value: unknown): value is CourseStatus => {
  return ['planned', 'in_progress', 'completed', 'failed'].includes(value as string);
};

/**
 * Type guard to check if a value is a valid ProgressStatus
 */
export const isProgressStatus = (value: unknown): value is ProgressStatus => {
  return ['not_started', 'in_progress', 'completed'].includes(value as string);
};