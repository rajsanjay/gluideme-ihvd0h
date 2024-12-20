'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

import { RequirementForm, requirementSchema } from '../../components/requirements/requirement-form';
import { LoadingSpinner } from '../../components/common/loading-spinner';
import { useRequirements } from '../../hooks/useRequirements';
import { useToast } from '../../hooks/useToast';
import { ErrorBoundary } from '../../components/common/error-boundary';
import type { TransferRequirement } from '../../types/requirements';

/**
 * EditRequirementPage component for editing existing transfer requirements
 * Implements form validation, error handling, and accessibility features
 */
const EditRequirementPage: React.FC = () => {
  // Get requirement ID from route parameters
  const params = useParams();
  const requirementId = params.id as string;

  // Initialize hooks
  const router = useRouter();
  const toast = useToast();
  const [isLoading, setIsLoading] = useState(true);
  const [requirement, setRequirement] = useState<TransferRequirement | null>(null);

  // Initialize requirements hook with optimistic updates
  const { 
    operations: { update: updateRequirement },
    isUpdating 
  } = useRequirements();

  // Fetch requirement data on component mount
  useEffect(() => {
    const fetchRequirement = async () => {
      try {
        const response = await fetch(`/api/v1/requirements/${requirementId}`);
        if (!response.ok) {
          throw new Error('Failed to fetch requirement');
        }
        const data = await response.json();
        setRequirement(data);
      } catch (error) {
        toast.show({
          type: 'error',
          message: 'Failed to load requirement details',
          duration: 5000
        });
        router.push('/dashboard/requirements');
      } finally {
        setIsLoading(false);
      }
    };

    fetchRequirement();
  }, [requirementId, router, toast]);

  /**
   * Handles form submission with validation and optimistic updates
   */
  const handleSubmit = async (formData: TransferRequirement) => {
    try {
      // Validate form data against schema
      const validatedData = await requirementSchema.parseAsync(formData);

      // Optimistically update UI
      const previousData = requirement;
      setRequirement(validatedData);

      // Attempt to update requirement
      await updateRequirement(requirementId, validatedData);

      toast.show({
        type: 'success',
        message: 'Requirement updated successfully',
        duration: 5000
      });

      // Navigate back to requirements list
      router.push('/dashboard/requirements');
    } catch (error) {
      // Rollback optimistic update on error
      if (requirement) {
        setRequirement(requirement);
      }

      toast.show({
        type: 'error',
        message: 'Failed to update requirement',
        duration: 5000
      });
    }
  };

  // Show loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner 
          size="lg"
          color="primary"
          aria-label="Loading requirement details"
        />
      </div>
    );
  }

  // Show error if requirement not found
  if (!requirement) {
    return (
      <div className="p-6 text-center">
        <h1 className="text-2xl font-bold text-red-600">
          Requirement not found
        </h1>
        <button
          onClick={() => router.push('/dashboard/requirements')}
          className="mt-4 px-4 py-2 bg-primary text-white rounded hover:bg-primary-dark"
        >
          Return to Requirements
        </button>
      </div>
    );
  }

  return (
    <ErrorBoundary
      fallback={
        <div className="p-6 text-center">
          <h1 className="text-2xl font-bold text-red-600">
            Something went wrong
          </h1>
          <button
            onClick={() => router.push('/dashboard/requirements')}
            className="mt-4 px-4 py-2 bg-primary text-white rounded hover:bg-primary-dark"
          >
            Return to Requirements
          </button>
        </div>
      }
    >
      <div className="container mx-auto px-4 py-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">
            Edit Transfer Requirement
          </h1>
          <button
            onClick={() => router.push('/dashboard/requirements')}
            className="px-4 py-2 text-gray-600 hover:text-gray-800"
            aria-label="Return to requirements list"
          >
            Cancel
          </button>
        </div>

        <RequirementForm
          initialValues={requirement}
          onSubmit={handleSubmit}
          isEdit={true}
          onCancel={() => router.push('/dashboard/requirements')}
          autoSave={false}
        />

        {isUpdating && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
            <LoadingSpinner 
              size="lg"
              color="white"
              aria-label="Saving requirement changes"
            />
          </div>
        )}
      </div>
    </ErrorBoundary>
  );
};

export default EditRequirementPage;