'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { ErrorBoundary } from 'react-error-boundary'; // v4.0.0
import { RequirementForm } from '../../../../../components/requirements/requirement-form';
import { RequirementCard } from '../../../../../components/requirements/requirement-card';
import { getRequirementById, updateRequirement } from '../../../../../lib/api/requirements';
import { useToast } from '../../../../../hooks/useToast';
import type { TransferRequirement } from '../../../../../types/requirements';
import { Card } from '../../../../../components/common/card';

/**
 * RequirementPage component for displaying and editing transfer requirements
 * Implements comprehensive error handling, accessibility features, and optimistic updates
 */
const RequirementPage: React.FC = () => {
  // Get requirement ID from route parameters
  const params = useParams();
  const id = params.id as string;

  // State management
  const [requirement, setRequirement] = useState<TransferRequirement | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Toast notifications
  const toast = useToast();

  /**
   * Fetches requirement details with error handling
   */
  const fetchRequirement = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await getRequirementById(id);
      setRequirement(response.data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load requirement';
      setError(message);
      toast.show({
        type: 'error',
        message: 'Failed to load requirement details'
      });
    } finally {
      setIsLoading(false);
    }
  }, [id, toast]);

  // Initial data fetch
  useEffect(() => {
    fetchRequirement();
  }, [fetchRequirement]);

  /**
   * Handles requirement updates with optimistic updates and error handling
   */
  const handleUpdateRequirement = useCallback(async (updatedRequirement: TransferRequirement) => {
    if (!requirement) return;

    // Store previous state for rollback
    const previousRequirement = requirement;

    try {
      // Optimistic update
      setRequirement(updatedRequirement);
      setIsEditing(false);

      // Perform update
      await updateRequirement(id, updatedRequirement);

      toast.show({
        type: 'success',
        message: 'Requirement updated successfully'
      });
    } catch (err) {
      // Rollback on error
      setRequirement(previousRequirement);
      setIsEditing(true);

      const message = err instanceof Error ? err.message : 'Failed to update requirement';
      toast.show({
        type: 'error',
        message: `Update failed: ${message}`
      });
    }
  }, [id, requirement, toast]);

  /**
   * Error fallback component
   */
  const ErrorFallback = useCallback(({ error, resetErrorBoundary }: any) => (
    <Card
      variant="outline"
      className="p-6 bg-red-50 dark:bg-red-900"
      role="alert"
    >
      <h2 className="text-lg font-semibold text-red-800 dark:text-red-100 mb-2">
        Error Loading Requirement
      </h2>
      <p className="text-red-600 dark:text-red-200 mb-4">
        {error.message}
      </p>
      <button
        onClick={resetErrorBoundary}
        className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
      >
        Try Again
      </button>
    </Card>
  ), []);

  /**
   * Loading state component
   */
  if (isLoading) {
    return (
      <div 
        className="p-6 animate-pulse"
        role="status"
        aria-label="Loading requirement details"
      >
        <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-4" />
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-2/3 mb-2" />
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
      </div>
    );
  }

  /**
   * Error state component
   */
  if (error) {
    return (
      <Card
        variant="outline"
        className="p-6 bg-red-50 dark:bg-red-900"
        role="alert"
      >
        <h2 className="text-lg font-semibold text-red-800 dark:text-red-100 mb-2">
          Error
        </h2>
        <p className="text-red-600 dark:text-red-200 mb-4">{error}</p>
        <button
          onClick={fetchRequirement}
          className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
        >
          Retry
        </button>
      </Card>
    );
  }

  return (
    <ErrorBoundary FallbackComponent={ErrorFallback} onReset={fetchRequirement}>
      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-semibold">
            {isEditing ? 'Edit Requirement' : 'Requirement Details'}
          </h1>
          {!isEditing && requirement && (
            <button
              onClick={() => setIsEditing(true)}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              aria-label="Edit requirement"
            >
              Edit
            </button>
          )}
        </div>

        {/* Content */}
        {requirement && (
          <div className="space-y-6">
            {isEditing ? (
              <RequirementForm
                initialValues={requirement}
                onSubmit={handleUpdateRequirement}
                onCancel={() => setIsEditing(false)}
                isEdit
              />
            ) : (
              <RequirementCard
                requirement={requirement}
                className="w-full"
              />
            )}
          </div>
        )}
      </div>
    </ErrorBoundary>
  );
};

export default RequirementPage;