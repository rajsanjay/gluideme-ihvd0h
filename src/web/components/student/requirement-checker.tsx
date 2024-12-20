/**
 * @file RequirementChecker Component
 * @version 1.0.0
 * @description Real-time course validation component that checks student course selections
 * against transfer requirements with 99.99% accuracy target. Implements debounced validation,
 * result caching, and comprehensive error handling.
 */

import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useDebounce } from 'use-debounce'; // v9.0.0
import { useLocalStorage } from '@rehooks/local-storage'; // v2.4.4
import { cn } from 'class-variance-authority'; // v0.7.0

import type { TransferRequirement } from '../../types/requirements';
import { validateCourse } from '../../lib/api/validation';
import LoadingSpinner from '../common/loading-spinner';
import Card from '../common/card';

// Validation result interface
interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  progress: ValidationProgress;
  timestamp: number;
}

// Validation error interface
interface ValidationError {
  code: string;
  message: string;
  field?: string;
  details?: Record<string, unknown>;
}

// Progress tracking interface
interface ValidationProgress {
  completedRequirements: number;
  totalRequirements: number;
  percentageComplete: number;
  remainingCredits: number;
}

// Component props interface
interface RequirementCheckerProps {
  requirement: TransferRequirement;
  selectedCourses: string[];
  institutionId: string;
  onValidationComplete?: (result: ValidationResult) => void;
  cacheKey?: string;
  validationDelay?: number;
}

/**
 * RequirementChecker Component
 * 
 * Validates selected courses against transfer requirements in real-time,
 * providing immediate feedback and progress tracking.
 */
const RequirementChecker: React.FC<RequirementCheckerProps> = ({
  requirement,
  selectedCourses,
  institutionId,
  onValidationComplete,
  cacheKey = 'validation-cache',
  validationDelay = 500
}) => {
  // Component state
  const [validationStatus, setValidationStatus] = useState<ValidationResult | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Cache validation results
  const [cachedResults, setCachedResults] = useLocalStorage<Record<string, ValidationResult>>(
    cacheKey,
    {}
  );

  // Debounce selected courses to prevent excessive validation calls
  const [debouncedCourses] = useDebounce(selectedCourses, validationDelay);

  // Abort controller for cleanup
  const abortControllerRef = useRef<AbortController | null>(null);

  /**
   * Validates selected courses against requirements with caching
   */
  const validateSelectedCourses = useCallback(async (
    courses: string[],
    requirementId: string,
    signal: AbortSignal
  ): Promise<ValidationResult> => {
    // Generate cache key for current validation
    const validationCacheKey = `${requirementId}-${courses.sort().join('-')}`;
    
    // Check cache for existing valid result
    const cachedResult = cachedResults[validationCacheKey];
    if (cachedResult && Date.now() - cachedResult.timestamp < 5 * 60 * 1000) {
      return cachedResult;
    }

    try {
      // Validate each course in parallel
      const validationPromises = courses.map(courseId => 
        validateCourse({
          courseId,
          requirementId,
          institutionId,
        })
      );

      const results = await Promise.all(validationPromises);

      // Aggregate validation results
      const validationResult: ValidationResult = {
        isValid: results.every(r => r.data.isValid),
        errors: results.flatMap(r => r.data.errors),
        progress: calculateProgress(results, requirement.rules),
        timestamp: Date.now()
      };

      // Cache successful validation
      setCachedResults(prev => ({
        ...prev,
        [validationCacheKey]: validationResult
      }));

      return validationResult;
    } catch (err) {
      if (signal.aborted) {
        throw new Error('Validation aborted');
      }
      throw err;
    }
  }, [cachedResults, institutionId, requirement.rules, setCachedResults]);

  /**
   * Calculate validation progress
   */
  const calculateProgress = (
    results: any[],
    rules: TransferRequirement['rules']
  ): ValidationProgress => {
    const totalRequirements = rules.rules.length;
    const completedRequirements = results.filter(r => r.data.isValid).length;
    const remainingCredits = rules.totalCredits - results.reduce((acc, r) => 
      acc + (r.data.isValid ? r.data.details.credits || 0 : 0), 0
    );

    return {
      completedRequirements,
      totalRequirements,
      percentageComplete: (completedRequirements / totalRequirements) * 100,
      remainingCredits
    };
  };

  // Effect for handling validation
  useEffect(() => {
    if (!debouncedCourses.length) {
      setValidationStatus(null);
      return;
    }

    const runValidation = async () => {
      // Cleanup previous validation
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      const controller = new AbortController();
      abortControllerRef.current = controller;

      setIsValidating(true);
      setError(null);

      try {
        const result = await validateSelectedCourses(
          debouncedCourses,
          requirement.id,
          controller.signal
        );

        setValidationStatus(result);
        onValidationComplete?.(result);
      } catch (err) {
        if (!controller.signal.aborted) {
          setError('Validation failed. Please try again.');
          console.error('Validation error:', err);
        }
      } finally {
        if (!controller.signal.aborted) {
          setIsValidating(false);
        }
      }
    };

    runValidation();

    return () => {
      abortControllerRef.current?.abort();
    };
  }, [debouncedCourses, requirement.id, validateSelectedCourses, onValidationComplete]);

  return (
    <Card
      variant="outline"
      padding="lg"
      className={cn(
        'w-full transition-all',
        isValidating && 'opacity-90'
      )}
    >
      {/* Validation Status Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">
          Requirement Validation Status
        </h3>
        {isValidating && (
          <LoadingSpinner 
            size="sm"
            color="primary"
            className="ml-2"
          />
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-md">
          {error}
        </div>
      )}

      {/* Validation Results */}
      {validationStatus && (
        <div className="space-y-4">
          {/* Progress Bar */}
          <div className="w-full bg-gray-100 dark:bg-gray-800 rounded-full h-2.5">
            <div
              className={cn(
                'h-full rounded-full transition-all',
                validationStatus.isValid
                  ? 'bg-green-500'
                  : 'bg-yellow-500'
              )}
              style={{
                width: `${validationStatus.progress.percentageComplete}%`
              }}
            />
          </div>

          {/* Progress Stats */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">Completed Requirements</p>
              <p className="font-medium">
                {validationStatus.progress.completedRequirements} of{' '}
                {validationStatus.progress.totalRequirements}
              </p>
            </div>
            <div>
              <p className="text-muted-foreground">Remaining Credits</p>
              <p className="font-medium">
                {validationStatus.progress.remainingCredits}
              </p>
            </div>
          </div>

          {/* Validation Errors */}
          {validationStatus.errors.length > 0 && (
            <div className="mt-4">
              <h4 className="font-medium mb-2">Validation Issues</h4>
              <ul className="space-y-2">
                {validationStatus.errors.map((error, index) => (
                  <li
                    key={`${error.code}-${index}`}
                    className="text-sm text-red-600 dark:text-red-400"
                  >
                    {error.message}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </Card>
  );
};

export default RequirementChecker;