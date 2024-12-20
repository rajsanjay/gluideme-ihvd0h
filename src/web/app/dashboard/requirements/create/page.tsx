"use client";

import React, { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ErrorBoundary } from 'react-error-boundary';
import MainLayout from '../../../../components/layout/main-layout';
import { RequirementForm } from '../../../../components/requirements/requirement-form';
import { useRequirements } from '../../../../hooks/useRequirements';
import { useToast } from '../../../../hooks/useToast';
import type { TransferRequirement } from '../../../../types/requirements';
import { ROUTE_PATHS } from '../../../../config/routes';

/**
 * CreateRequirementPage Component
 * 
 * A comprehensive page component for creating new transfer requirements with
 * real-time validation, error handling, and accessibility features.
 */
const CreateRequirementPage: React.FC = () => {
  // Initialize hooks
  const router = useRouter();
  const toast = useToast();
  const { operations } = useRequirements();
  
  // Track form state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formKey, setFormKey] = useState(Date.now());

  // Handle cleanup on unmount
  useEffect(() => {
    return () => {
      // Clear any form-related local storage
      localStorage.removeItem('requirement-form-draft');
    };
  }, []);

  /**
   * Handles form submission with comprehensive error handling
   * and optimistic updates
   */
  const handleSubmit = useCallback(async (requirement: TransferRequirement) => {
    try {
      setIsSubmitting(true);

      // Create new requirement
      await operations.create({
        ...requirement,
        status: 'draft',
        metadata: {
          ...requirement.metadata,
          createdAt: new Date().toISOString(),
          lastModified: new Date().toISOString()
        }
      });

      // Show success notification
      toast.show({
        message: 'Transfer requirement created successfully',
        type: 'success',
        duration: 5000
      });

      // Navigate to requirements list
      router.push(ROUTE_PATHS.REQUIREMENTS);
    } catch (error) {
      console.error('Failed to create requirement:', error);
      
      // Show error notification with details
      toast.show({
        message: 'Failed to create requirement. Please try again.',
        type: 'error',
        duration: 7000
      });

      // Reset form state
      setIsSubmitting(false);
      setFormKey(Date.now());
    }
  }, [operations, router, toast]);

  /**
   * Handles cancellation and navigation
   */
  const handleCancel = useCallback(() => {
    // Show confirmation if form is dirty
    if (localStorage.getItem('requirement-form-draft')) {
      const confirmed = window.confirm(
        'Are you sure you want to cancel? Any unsaved changes will be lost.'
      );
      if (!confirmed) return;
    }

    // Clear draft and navigate back
    localStorage.removeItem('requirement-form-draft');
    router.push(ROUTE_PATHS.REQUIREMENTS);
  }, [router]);

  return (
    <ErrorBoundary
      fallback={
        <div className="p-4 text-red-500">
          <h2 className="text-lg font-semibold">Error</h2>
          <p>An error occurred while loading the requirement form.</p>
          <button 
            onClick={() => router.push(ROUTE_PATHS.REQUIREMENTS)}
            className="mt-4 text-blue-500 hover:text-blue-700"
          >
            Return to Requirements
          </button>
        </div>
      }
    >
      <MainLayout>
        <div className="container mx-auto px-4 py-8">
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              Create Transfer Requirement
            </h1>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              Define a new transfer requirement with course equivalencies and validation rules.
            </p>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
            <RequirementForm
              key={formKey}
              onSubmit={handleSubmit}
              onCancel={handleCancel}
              autoSave={true}
              isEdit={false}
            />
          </div>
        </div>
      </MainLayout>
    </ErrorBoundary>
  );
};

export default CreateRequirementPage;