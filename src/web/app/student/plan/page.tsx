"use client";

import React, { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { reportWebVitals } from 'next/web-vitals';
import { analytics } from '@vercel/analytics';
import { PlanForm, type PlanFormProps } from '../../../../components/student/plan-form';
import CourseList from '../../../../components/student/course-list';
import ProgressTracker from '../../../../components/student/progress-tracker';
import { useRequirements } from '../../../../hooks/useRequirements';
import ErrorBoundary from '../../../../components/common/error-boundary';
import { useToast } from '../../../../hooks/useToast';
import type { PlannedCourse, CourseStatus, TransferPlan, TransferProgress } from '../../../../types/student';

/**
 * StudentPlanPage component for managing student transfer plans
 * Implements comprehensive course planning and progress tracking functionality
 */
const StudentPlanPage: React.FC = () => {
  // Initialize hooks
  const router = useRouter();
  const toast = useToast();
  const { operations } = useRequirements();

  // State management
  const [isLoading, setIsLoading] = useState(true);
  const [plan, setPlan] = useState<TransferPlan | null>(null);
  const [isEditing, setIsEditing] = useState(false);

  // Load plan data
  useEffect(() => {
    const loadPlan = async () => {
      try {
        // In a real implementation, this would fetch from an API
        // For now, using mock data
        const mockPlan: TransferPlan = {
          id: '1',
          studentId: '1',
          requirementId: '1',
          targetInstitutionId: '1',
          status: 'draft',
          courses: [],
          progress: {
            overallStatus: 'in_progress',
            completedUnits: 0,
            requiredUnits: 60,
            currentGPA: 0,
            requirementProgress: []
          },
          notes: '',
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString()
        };
        setPlan(mockPlan);
      } catch (error) {
        console.error('Failed to load plan:', error);
        toast.show({
          type: 'error',
          message: 'Failed to load transfer plan'
        });
      } finally {
        setIsLoading(false);
      }
    };

    loadPlan();
    // Track page view
    analytics.track('view_transfer_plan');
  }, [toast]);

  // Handle course status changes
  const handleCourseStatusChange = useCallback(async (
    courseId: string,
    newStatus: CourseStatus
  ) => {
    try {
      analytics.track('update_course_status', { courseId, newStatus });
      setIsLoading(true);

      // Optimistic update
      setPlan(prevPlan => {
        if (!prevPlan) return null;
        return {
          ...prevPlan,
          courses: prevPlan.courses.map(course =>
            course.courseId === courseId ? { ...course, status: newStatus } : course
          )
        };
      });

      // Validate updated courses
      const updatedCourses = plan?.courses.map(c => c.courseId) || [];
      await operations.validate(plan?.requirementId || '', updatedCourses);

      toast.show({
        type: 'success',
        message: 'Course status updated successfully'
      });
    } catch (error) {
      console.error('Failed to update course status:', error);
      toast.show({
        type: 'error',
        message: 'Failed to update course status'
      });
    } finally {
      setIsLoading(false);
    }
  }, [plan, operations, toast]);

  // Handle grade updates
  const handleGradeUpdate = useCallback(async (
    courseId: string,
    newGrade: string
  ) => {
    try {
      analytics.track('update_course_grade', { courseId, grade: newGrade });
      setIsLoading(true);

      // Optimistic update
      setPlan(prevPlan => {
        if (!prevPlan) return null;
        return {
          ...prevPlan,
          courses: prevPlan.courses.map(course =>
            course.courseId === courseId ? { ...course, grade: newGrade } : course
          )
        };
      });

      // In real implementation, this would call an API
      toast.show({
        type: 'success',
        message: 'Grade updated successfully'
      });
    } catch (error) {
      console.error('Failed to update grade:', error);
      toast.show({
        type: 'error',
        message: 'Failed to update grade'
      });
    } finally {
      setIsLoading(false);
    }
  }, [toast]);

  // Handle plan form submission
  const handlePlanSubmit = useCallback(async (data: PlanFormProps['initialData']) => {
    try {
      analytics.track('submit_transfer_plan', { planId: plan?.id });
      setIsLoading(true);

      // In real implementation, this would call an API
      setPlan(prevPlan => {
        if (!prevPlan) return null;
        return {
          ...prevPlan,
          ...data,
          updatedAt: new Date().toISOString()
        };
      });

      setIsEditing(false);
      toast.show({
        type: 'success',
        message: 'Plan updated successfully'
      });
    } catch (error) {
      console.error('Failed to update plan:', error);
      toast.show({
        type: 'error',
        message: 'Failed to update plan'
      });
    } finally {
      setIsLoading(false);
    }
  }, [plan, toast]);

  // Performance monitoring
  useEffect(() => {
    reportWebVitals(metric => {
      analytics.track('web_vital', {
        name: metric.name,
        value: metric.value,
        page: 'student_plan'
      });
    });
  }, []);

  return (
    <ErrorBoundary
      fallback={
        <div className="p-4 text-center">
          <h2 className="text-xl font-semibold text-red-600">
            Something went wrong
          </h2>
          <button
            onClick={() => router.refresh()}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Retry
          </button>
        </div>
      }
    >
      <div className="container mx-auto px-4 py-8 space-y-8">
        <h1 className="text-3xl font-bold">Transfer Plan</h1>

        {isLoading ? (
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-gray-200 rounded w-1/4" />
            <div className="h-64 bg-gray-200 rounded" />
          </div>
        ) : (
          <>
            {isEditing ? (
              <PlanForm
                initialData={plan || undefined}
                onSubmit={handlePlanSubmit}
                onCancel={() => setIsEditing(false)}
                autoValidate
                validationConfig={{
                  validateOnBlur: true,
                  validateOnChange: false,
                  debounceMs: 300
                }}
                a11yConfig={{
                  announceValidation: true,
                  autoFocus: true
                }}
              />
            ) : (
              <button
                onClick={() => setIsEditing(true)}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                aria-label="Edit transfer plan"
              >
                Edit Plan
              </button>
            )}

            {plan && (
              <>
                <CourseList
                  courses={plan.courses}
                  loading={isLoading}
                  onStatusChange={handleCourseStatusChange}
                  onGradeUpdate={handleGradeUpdate}
                  virtualizeRows
                  accessibilityAnnouncements
                  showProgress
                />

                <ProgressTracker
                  progress={plan.progress}
                  className="mt-8"
                />
              </>
            )}
          </>
        )}
      </div>
    </ErrorBoundary>
  );
};

export default StudentPlanPage;