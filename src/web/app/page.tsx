"use client";

import React, { useCallback, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from '@shadcn/ui';
import MainLayout from '../components/layout/main-layout';
import SearchForm from '../components/search/search-form';
import LoginForm from '../components/auth/login-form';
import { useAuth } from '../hooks/useAuth';
import type { SearchType, SearchFilters } from '../types/search';

/**
 * HomePage Component
 * 
 * The main landing page for the Transfer Requirements Management System.
 * Implements a responsive, accessible interface with search functionality
 * and authentication options.
 */
const HomePage: React.FC = () => {
  const router = useRouter();
  const { state: authState } = useAuth();
  const announcementRef = useRef<HTMLDivElement>(null);

  // Track initial page load for analytics
  useEffect(() => {
    // Implementation would integrate with your analytics system
    console.log('Home page viewed:', {
      timestamp: new Date(),
      authenticated: authState.isAuthenticated
    });
  }, [authState.isAuthenticated]);

  /**
   * Handle search form submission
   */
  const handleSearch = useCallback(async (
    query: string,
    type: SearchType,
    filters: SearchFilters
  ) => {
    try {
      // Construct search URL with parameters
      const searchParams = new URLSearchParams({
        q: query,
        type,
        ...Object.entries(filters).reduce((acc, [key, value]) => ({
          ...acc,
          [key]: typeof value === 'object' ? JSON.stringify(value) : value
        }), {})
      });

      // Navigate to search results
      router.push(`/search?${searchParams.toString()}`);
    } catch (error) {
      console.error('Search error:', error);
      toast({
        title: 'Search Error',
        description: 'Failed to perform search. Please try again.',
        variant: 'destructive'
      });
    }
  }, [router]);

  /**
   * Handle successful login
   */
  const handleLoginSuccess = useCallback(() => {
    router.push('/dashboard');
    toast({
      title: 'Welcome back!',
      description: 'You have successfully logged in.',
      variant: 'default'
    });
  }, [router]);

  return (
    <MainLayout>
      <div className="flex flex-col min-h-screen">
        {/* Hero Section */}
        <section className="relative py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-primary-50 to-white dark:from-primary-900 dark:to-background">
          <div className="max-w-7xl mx-auto">
            <div className="text-center">
              <h1 className="text-4xl font-extrabold tracking-tight text-gray-900 dark:text-white sm:text-5xl md:text-6xl">
                <span className="block">Transfer Requirements</span>
                <span className="block text-primary-600 dark:text-primary-400">
                  Management System
                </span>
              </h1>
              <p className="mt-3 max-w-md mx-auto text-base text-gray-500 dark:text-gray-400 sm:text-lg md:mt-5 md:text-xl md:max-w-3xl">
                Streamline and automate the process of managing course transfer
                requirements between California community colleges and 4-year
                institutions.
              </p>
            </div>

            {/* Search Section */}
            <div className="mt-10 max-w-3xl mx-auto">
              <SearchForm
                onSearch={handleSearch}
                className="w-full"
                analyticsEnabled={true}
              />
              {/* Screen reader announcements */}
              <div
                ref={announcementRef}
                className="sr-only"
                role="status"
                aria-live="polite"
              />
            </div>
          </div>
        </section>

        {/* Authentication Section */}
        <section className="py-12 px-4 sm:px-6 lg:px-8 bg-white dark:bg-gray-800">
          <div className="max-w-md mx-auto">
            {!authState.isAuthenticated ? (
              <div className="space-y-8">
                <div className="text-center">
                  <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
                    Sign in to your account
                  </h2>
                  <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                    Access your transfer requirements and planning tools
                  </p>
                </div>
                <LoginForm
                  onSuccess={handleLoginSuccess}
                  onError={(error) => {
                    toast({
                      title: 'Authentication Error',
                      description: error.message,
                      variant: 'destructive'
                    });
                  }}
                  className="mt-8"
                />
              </div>
            ) : (
              <div className="text-center">
                <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">
                  Welcome back, {authState.user?.email}
                </h2>
                <p className="mt-2 text-gray-600 dark:text-gray-400">
                  Continue managing transfer requirements
                </p>
                <button
                  onClick={() => router.push('/dashboard')}
                  className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                >
                  Go to Dashboard
                </button>
              </div>
            )}
          </div>
        </section>
      </div>
    </MainLayout>
  );
};

export default HomePage;