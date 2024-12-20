"use client";

import React, { useEffect, useCallback } from 'react';
import { Analytics } from '@aws-amplify/analytics';
import { redirect } from 'next/navigation';
import MainLayout from '../../../components/layout/main-layout';
import { useAuth } from '../../../hooks/useAuth';

// Version: ^6.0.0 - @aws-amplify/analytics
// Version: ^13.0.0 - next/navigation
// Version: ^18.2.0 - react

/**
 * Props interface for DashboardLayout component with enhanced typing
 */
interface DashboardLayoutProps {
  children: React.ReactNode;
  requiredRole?: string[];
  metadata?: DashboardMetadata;
}

/**
 * Metadata interface for dashboard SEO and analytics
 */
interface DashboardMetadata {
  title: string;
  description: string;
  analyticsData?: Record<string, any>;
}

/**
 * Enhanced dashboard layout wrapper component that provides the base structure
 * for all dashboard pages with role-based access control, analytics integration,
 * and security features.
 */
const DashboardLayout = React.memo(({ 
  children,
  requiredRole = ['admin', 'institution_admin'],
  metadata = {
    title: 'Dashboard',
    description: 'Transfer Requirements Management System Dashboard'
  }
}: DashboardLayoutProps) => {
  // Get authentication state and user information
  const { state: authState, user, loading, error, checkPermission } = useAuth();

  /**
   * Initialize analytics for dashboard session tracking
   */
  useEffect(() => {
    Analytics.configure({
      disabled: process.env.NODE_ENV === 'development',
      autoSessionTracking: true,
      region: process.env.NEXT_PUBLIC_AWS_REGION
    });
  }, []);

  /**
   * Track dashboard session and user activity
   */
  const trackDashboardActivity = useCallback(() => {
    if (user) {
      Analytics.record({
        name: 'DashboardView',
        attributes: {
          userId: user.id,
          role: user.role,
          institutionId: user.institutionId || 'none',
          ...metadata.analyticsData
        }
      });
    }
  }, [user, metadata.analyticsData]);

  /**
   * Verify authentication and role-based access
   */
  useEffect(() => {
    // Redirect to login if not authenticated
    if (!loading && !authState.isAuthenticated) {
      redirect('/login?redirect=/dashboard');
    }

    // Verify role-based access
    if (!loading && user) {
      const hasAccess = requiredRole.some(role => 
        role === '*' || checkPermission(`access_${role}`)
      );

      if (!hasAccess) {
        Analytics.record({
          name: 'UnauthorizedAccess',
          attributes: {
            userId: user.id,
            role: user.role,
            requiredRole: requiredRole.join(',')
          }
        });
        redirect('/unauthorized');
      }

      // Track successful access
      trackDashboardActivity();
    }
  }, [loading, authState.isAuthenticated, user, requiredRole, checkPermission, trackDashboardActivity]);

  /**
   * Handle authentication errors
   */
  useEffect(() => {
    if (error) {
      Analytics.record({
        name: 'AuthenticationError',
        attributes: {
          error: error.toString(),
          path: '/dashboard'
        }
      });
      redirect('/login?error=session_expired');
    }
  }, [error]);

  // Show loading state
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="animate-spin h-8 w-8 border-4 border-primary-500 rounded-full border-t-transparent" />
      </div>
    );
  }

  return (
    <MainLayout
      className="min-h-screen bg-background"
      // Set metadata for SEO and accessibility
      aria-label="Dashboard Layout"
      role="main"
    >
      {/* Error boundary for dashboard content */}
      <React.Suspense
        fallback={
          <div className="flex min-h-screen items-center justify-center">
            <div className="animate-spin h-8 w-8 border-4 border-primary-500 rounded-full border-t-transparent" />
          </div>
        }
      >
        {/* Dashboard content */}
        <div className="container mx-auto px-4 py-8">
          <header className="mb-8">
            <h1 className="text-2xl font-bold text-foreground">
              {metadata.title}
            </h1>
            <p className="mt-2 text-muted-foreground">
              {metadata.description}
            </p>
          </header>

          {/* Main content area */}
          <main className="relative">
            {children}
          </main>
        </div>
      </React.Suspense>
    </MainLayout>
  );
});

// Set display name for development
DashboardLayout.displayName = 'DashboardLayout';

export default DashboardLayout;