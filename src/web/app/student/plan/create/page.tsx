"use client";

import React, { useCallback, useState } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner'; // v1.0.0
import { useAnalytics } from '@vercel/analytics'; // v1.0.0
import { ErrorBoundary } from 'react-error-boundary'; // v4.0.0

import MainLayout from '../../../../components/layout/main-layout';
import { PlanForm } from '../../../../components/student/plan-form';
import { useAuth } from '../../../../hooks/useAuth';
import type { TransferPlan } from '../../../../types/requirements';

/**
 * CreatePlanPage Component
 * 
 * A page component for creating new student transfer plans with real-time
 * validation, progress tracking, and comprehensive error handling.
 */
const CreatePlanPage: React.FC = () => {
  // Initialize hooks
  const router = useRouter();
  const { state: authState, user } = useAuth();
  const { track } = useAnalytics();
  const [isSubmitting, setIsSubmitting] = useState(false);

  /**
   * Handles form submission with validation and error tracking
   */
  const handleSubmit = useCallback(async (plan: TransferPlan) => {
    if (!user) {
      toast.error('Authentication required');
      router.push('/login');
      return;
    }

    setIsSubmitting(true);

    try {
      // Track form submission attempt
      track('transfer_plan_create_attempt', {
        userId: user.id,
        institutionId: plan.targetInstitutionId,
        majorCode: plan.majorCode
      });

      // Submit plan to API
      const response = await fetch('/api/v1/student/plans', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authState.accessToken}`
        },
        body: JSON.stringify({
          ...plan,
          studentId: user.id,
          status: 'draft',
          createdAt: new Date().toISOString()
        })
      });

      if (!response.ok) {
        throw new Error('Failed to create transfer plan');
      }

      // Track successful creation
      track('transfer_plan_create_success', {
        userId: user.id,
        planId: await response.json().then(data => data.id)
      });

      // Show success message
      toast.success('Transfer plan created successfully');

      // Redirect to plan details page
      router.push('/student/plan');
    } catch (error) {
      console.error('Plan creation error:', error);
      
      // Track error
      track('transfer_plan_create_error', {
        userId: user.id,
        error: error instanceof Error ? error.message : 'Unknown error'
      });

      // Show error message
      toast.error('Failed to create transfer plan. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  }, [user, authState.accessToken, router, track]);

  /**
   * Handles form cancellation
   */
  const handleCancel = useCallback(async () => {
    // Track cancellation
    if (user) {
      track('transfer_plan_create_cancel', {
        userId: user.id
      });
    }

    // Return to plans list
    router.push('/student/plan');
  }, [user, router, track]);

  // Render error fallback UI
  const renderError = ({ error, resetErrorBoundary }: { 
    error: Error; 
    resetErrorBoundary: () => void;
  }) => (
    <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
      <h2 className="text-lg font-semibold text-red-800 mb-2">
        Error Creating Plan
      </h2>
      <p className="text-red-600 mb-4">
        {error.message || 'An unexpected error occurred'}
      </p>
      <button
        onClick={resetErrorBoundary}
        className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
      >
        Try Again
      </button>
    </div>
  );

  return (
    <MainLayout>
      <ErrorBoundary
        FallbackComponent={renderError}
        onReset={() => router.refresh()}
      >
        <div className="max-w-4xl mx-auto px-4 py-8">
          <h1 className="text-2xl font-bold mb-6">
            Create Transfer Plan
          </h1>

          <PlanForm
            studentId={user?.id || ''}
            onSubmit={handleSubmit}
            onCancel={handleCancel}
            autoValidate={true}
            validationConfig={{
              validateOnBlur: true,
              validateOnChange: false,
              debounceMs: 300
            }}
            a11yConfig={{
              announceValidation: true,
              autoFocus: true,
              preventSubmitOnEnter: true
            }}
          />

          {isSubmitting && (
            <div
              className="fixed inset-0 bg-black/50 flex items-center justify-center"
              aria-busy="true"
              aria-label="Creating plan..."
            >
              <div className="bg-white p-6 rounded-lg shadow-lg">
                <p className="text-lg">Creating your plan...</p>
              </div>
            </div>
          )}
        </div>
      </ErrorBoundary>
    </MainLayout>
  );
};

export default CreatePlanPage;