"use client";

import React, { useEffect, useState } from 'react';
import { notFound } from 'next/navigation';
import { ErrorBoundary } from 'react-error-boundary'; // ^4.0.0
import { Card } from '@shadcn/ui'; // ^0.1.0
import { useToast } from '@shadcn/ui'; // ^0.1.0
import { Skeleton } from '@shadcn/ui'; // ^0.1.0
import ProgressTracker from '../../../../components/student/progress-tracker';
import CourseList from '../../../../components/student/course-list';
import { getTransferPlan } from '../../../../lib/api/students';
import type { TransferPlan, CourseStatus } from '../../../../types/student';

// Props interface for the page component
interface PageProps {
  params: {
    id: string;
  };
  searchParams: {
    view?: string;
    term?: string;
  };
}

// Metadata generation for SEO
export async function generateMetadata({ params }: PageProps) {
  try {
    const response = await getTransferPlan('current', params.id);
    const plan = response.data;
    
    return {
      title: `Transfer Plan - ${plan.targetInstitutionId}`,
      description: `Transfer plan details and progress tracking for ${plan.targetInstitutionId}`,
      openGraph: {
        title: `Transfer Plan - ${plan.targetInstitutionId}`,
        description: `Track your transfer progress and requirements for ${plan.targetInstitutionId}`,
        type: 'website',
      },
    };
  } catch (error) {
    return {
      title: 'Transfer Plan',
      description: 'Student transfer plan details and progress tracking',
    };
  }
}

// Error fallback component
const ErrorFallback = ({ error, resetErrorBoundary }: { 
  error: Error; 
  resetErrorBoundary: () => void;
}) => (
  <Card className="p-6 text-center">
    <h2 className="text-lg font-semibold text-red-600 mb-2">Error Loading Plan</h2>
    <p className="text-gray-600 mb-4">{error.message}</p>
    <button
      onClick={resetErrorBoundary}
      className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
      aria-label="Retry loading transfer plan"
    >
      Try Again
    </button>
  </Card>
);

// Loading skeleton component
const LoadingSkeleton = () => (
  <div className="space-y-6">
    <Skeleton className="h-48 w-full" />
    <Skeleton className="h-96 w-full" />
  </div>
);

// Main page component
const TransferPlanPage: React.FC<PageProps> = ({ params, searchParams }) => {
  // State management
  const [plan, setPlan] = useState<TransferPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const { show: showToast } = useToast();

  // Fetch transfer plan data
  useEffect(() => {
    const fetchPlan = async () => {
      try {
        setLoading(true);
        const response = await getTransferPlan('current', params.id);
        setPlan(response.data);
      } catch (error) {
        showToast({
          title: "Error",
          description: "Failed to load transfer plan details",
          variant: "destructive",
        });
        if ((error as any)?.response?.status === 404) {
          notFound();
        }
      } finally {
        setLoading(false);
      }
    };

    fetchPlan();
  }, [params.id, showToast]);

  // Handle course status updates
  const handleStatusUpdate = async (courseId: string, status: CourseStatus) => {
    if (!plan) return;

    try {
      // Optimistic update
      const updatedCourses = plan.courses.map(course => 
        course.courseId === courseId ? { ...course, status } : course
      );

      setPlan({ ...plan, courses: updatedCourses });

      // API update would go here
      showToast({
        title: "Success",
        description: "Course status updated successfully",
        variant: "success",
      });
    } catch (error) {
      showToast({
        title: "Error",
        description: "Failed to update course status",
        variant: "destructive",
      });
    }
  };

  // Handle grade updates
  const handleGradeUpdate = async (courseId: string, grade: string) => {
    if (!plan) return;

    try {
      // Optimistic update
      const updatedCourses = plan.courses.map(course =>
        course.courseId === courseId ? { ...course, grade } : course
      );

      setPlan({ ...plan, courses: updatedCourses });

      // API update would go here
      showToast({
        title: "Success",
        description: "Grade updated successfully",
        variant: "success",
      });
    } catch (error) {
      showToast({
        title: "Error",
        description: "Failed to update grade",
        variant: "destructive",
      });
    }
  };

  if (loading) {
    return <LoadingSkeleton />;
  }

  return (
    <ErrorBoundary FallbackComponent={ErrorFallback} onReset={() => window.location.reload()}>
      <main className="container mx-auto px-4 py-8 space-y-8">
        {/* Header Section */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <h1 className="text-2xl font-bold text-gray-900">
            Transfer Plan Details
          </h1>
          <div className="flex items-center gap-2">
            <button
              onClick={() => window.print()}
              className="px-4 py-2 text-sm bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              aria-label="Print transfer plan"
            >
              Print Plan
            </button>
          </div>
        </div>

        {/* Progress Tracker */}
        {plan && (
          <ProgressTracker
            progress={plan.progress}
            className="mb-8"
            isRTL={false}
          />
        )}

        {/* Course List */}
        {plan && (
          <CourseList
            courses={plan.courses}
            onStatusChange={handleStatusUpdate}
            onGradeUpdate={handleGradeUpdate}
            className="mb-8"
            virtualizeRows
            accessibilityAnnouncements
            showProgress
          />
        )}

        {/* Notes Section */}
        {plan?.notes && (
          <Card className="p-6">
            <h2 className="text-lg font-semibold mb-2">Additional Notes</h2>
            <p className="text-gray-600 whitespace-pre-wrap">{plan.notes}</p>
          </Card>
        )}
      </main>
    </ErrorBoundary>
  );
};

export default TransferPlanPage;