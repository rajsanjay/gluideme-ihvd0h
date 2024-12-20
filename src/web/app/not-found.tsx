"use client";

import React from "react";
import { Button } from "../../components/common/button";
import { Card } from "../../components/common/card";
import { ROUTE_PATHS } from "../../config/routes";

/**
 * NotFound Component
 * 
 * A custom 404 error page that provides a user-friendly error message and navigation
 * options when users attempt to access non-existent routes. Implements WCAG 2.1 AA
 * accessibility standards with proper semantic structure and keyboard navigation.
 */
const NotFound: React.FC = () => {
  // Update document title for screen readers and SEO
  React.useEffect(() => {
    document.title = "Page Not Found - Transfer Requirements Management System";
  }, []);

  // Track 404 errors for monitoring
  React.useEffect(() => {
    // Log 404 error to analytics/monitoring system
    const path = window.location.pathname;
    console.error(`404 Error: Page not found - ${path}`);
  }, []);

  return (
    <main
      role="main"
      aria-labelledby="error-heading"
      className="min-h-screen w-full flex items-center justify-center p-4 bg-background"
    >
      <Card
        variant="elevated"
        padding="lg"
        className="max-w-lg w-full text-center"
        role="alert"
        aria-live="polite"
      >
        {/* Error Status */}
        <div className="mb-6">
          <span className="text-6xl font-bold text-primary-600 dark:text-primary-400">
            404
          </span>
        </div>

        {/* Error Message */}
        <h1
          id="error-heading"
          className="text-2xl font-semibold mb-4 text-foreground"
        >
          Page Not Found
        </h1>
        
        <p className="text-muted-foreground mb-8">
          The page you are looking for doesn't exist or has been moved.
          Please check the URL or return to the homepage.
        </p>

        {/* Navigation Button */}
        <Button
          variant="primary"
          size="lg"
          onClick={() => window.location.href = ROUTE_PATHS.HOME}
          aria-label="Return to homepage"
        >
          Return to Homepage
        </Button>

        {/* Additional Help Text */}
        <p className="mt-6 text-sm text-muted-foreground">
          If you believe this is an error, please{" "}
          <a
            href="/contact"
            className="text-primary-600 hover:underline focus:outline-none focus:ring-2 focus:ring-primary-500 rounded"
          >
            contact support
          </a>
          .
        </p>
      </Card>
    </main>
  );
};

export default NotFound;