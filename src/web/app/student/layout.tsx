"use client";

import React, { useCallback, useEffect } from 'react';
import { redirect, usePathname } from 'next/navigation';
import { cn } from 'class-variance-authority';

import MainLayout from '../../../components/layout/main-layout';
import RequirementChecker from '../../../components/student/requirement-checker';
import { useAuth } from '../../../hooks/useAuth';

/**
 * Props interface for StudentLayout component
 */
interface StudentLayoutProps {
  children: React.ReactNode;
  className?: string;
}

/**
 * StudentLayout Component
 * 
 * A layout wrapper for student-specific pages that implements role-based access control,
 * responsive design, and real-time requirement validation. Ensures only authenticated
 * students can access protected routes.
 */
const StudentLayout = React.memo<StudentLayoutProps>(({ 
  children,
  className 
}) => {
  // Get authentication state and current path
  const { 
    state: authState,
    user,
    isAuthenticated,
    loading: authLoading,
    error: authError 
  } = useAuth();
  const pathname = usePathname();

  /**
   * Validates user has student role and required permissions
   */
  const validateAccess = useCallback(() => {
    if (authLoading) return;

    // Redirect to login if not authenticated
    if (!isAuthenticated) {
      redirect('/login?redirect=' + encodeURIComponent(pathname));
    }

    // Redirect if not a student
    if (user?.role !== 'student') {
      redirect('/unauthorized');
    }

    // Handle auth errors
    if (authError) {
      console.error('Authentication error:', authError);
      redirect('/error');
    }
  }, [isAuthenticated, user?.role, authLoading, authError, pathname]);

  // Validate access on mount and auth state changes
  useEffect(() => {
    validateAccess();
  }, [validateAccess]);

  // Show loading state while checking auth
  if (authLoading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600" />
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout
      className={cn(
        'min-h-screen bg-background',
        'transition-colors duration-200',
        className
      )}
    >
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Main Content Area */}
          <main className="lg:col-span-8" role="main">
            {children}
          </main>

          {/* Sidebar with Requirement Checker */}
          <aside className="lg:col-span-4" role="complementary">
            {user && (
              <RequirementChecker
                requirement={user.currentRequirement}
                selectedCourses={user.selectedCourses}
                institutionId={user.institutionId}
                onValidationComplete={(result) => {
                  // Handle validation results
                  console.log('Validation complete:', result);
                }}
                validationDelay={500}
              />
            )}
          </aside>
        </div>
      </div>
    </MainLayout>
  );
});

// Set display name for dev tools
StudentLayout.displayName = 'StudentLayout';

export default StudentLayout;