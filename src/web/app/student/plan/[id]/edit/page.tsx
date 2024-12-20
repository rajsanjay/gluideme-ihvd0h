"use client";

import React, { useCallback, useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import MainLayout from '@/components/layout/main-layout';
import PlanForm from '@/components/student/plan-form';
import { useRequirements } from '@/hooks/useRequirements';
import { toast } from '@/lib/toast';

/**
 * EditPlanPage component for editing student transfer plans
 * Implements real-time validation, accessibility features, and comprehensive error handling
 */
const EditPlanPage: React.FC = () => {
  // Initialize router and params
  const router = useRouter();
  const params = useParams();
  const planId = params?.id as string;

  // Initialize state
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  // Initialize requirements hook
  const { 
    operations: { update: updateRequirement },
    isUpdating
  } = useRequirements();

  // Track unsaved changes
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  /**
   * Handle form submission with optimistic updates
   */
  const handleSubmit = useCallback(async (updatedPlan) => {
    try {
      // Show optimistic toast
      const toastId = toast.show({
        message: 'Saving changes...',
        type: 'info'
      });

      // Update requirement
      await updateRequirement(planId, updatedPlan);

      // Update toast on success
      toast.update({
        id: toastId,
        message: 'Changes saved successfully',
        type: 'success'
      });

      // Reset unsaved changes flag
      setHasUnsavedChanges(false);

      // Navigate back to plan view
      router.push(`/student/plan/${planId}`);
    } catch (error) {
      console.error('Failed to update plan:', error);
      
      // Show error toast
      toast.show({
        message: 'Failed to save changes. Please try again.',
        type: 'error',
        duration: 5000
      });

      // Set error state
      setError(error as Error);
    }
  }, [planId, router, updateRequirement]);

  /**
   * Handle form cancellation
   */
  const handleCancel = useCallback(() => {
    if (hasUnsavedChanges) {
      // Show confirmation dialog
      const confirmed = window.confirm(
        'You have unsaved changes. Are you sure you want to leave?'
      );
      if (!confirmed) return;
    }
    router.back();
  }, [hasUnsavedChanges, router]);

  /**
   * Handle unsaved changes warning
   */
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges) {
        e.preventDefault();
        e.returnValue = '';
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [hasUnsavedChanges]);

  /**
   * Fetch initial plan data
   */
  useEffect(() => {
    const fetchPlan = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // Fetch plan data here
        // const plan = await getPlanById(planId);
        // setPlan(plan);

      } catch (error) {
        console.error('Failed to fetch plan:', error);
        setError(error as Error);
        
        toast.show({
          message: 'Failed to load transfer plan',
          type: 'error',
          duration: 5000
        });
      } finally {
        setIsLoading(false);
      }
    };

    if (planId) {
      fetchPlan();
    }
  }, [planId]);

  return (
    <MainLayout>
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Page Header */}
          <div className="mb-8">
            <h1 className="text-2xl font-bold mb-2">
              Edit Transfer Plan
            </h1>
            <p className="text-gray-600">
              Update your transfer plan and course selections
            </p>
          </div>

          {/* Loading State */}
          {isLoading && (
            <div className="flex items-center justify-center py-12" role="status" aria-label="Loading">
              <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full" />
            </div>
          )}

          {/* Error State */}
          {error && (
            <div 
              className="bg-red-50 border border-red-200 rounded-md p-4 mb-8"
              role="alert"
            >
              <h2 className="text-red-800 font-semibold mb-2">
                Error Loading Plan
              </h2>
              <p className="text-red-600">
                {error.message}
              </p>
              <button
                onClick={() => window.location.reload()}
                className="mt-4 px-4 py-2 bg-red-100 text-red-800 rounded hover:bg-red-200"
              >
                Retry
              </button>
            </div>
          )}

          {/* Plan Form */}
          {!isLoading && !error && (
            <PlanForm
              studentId={planId}
              // initialData={plan}
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
          )}
        </div>
      </div>
    </MainLayout>
  );
};

export default EditPlanPage;