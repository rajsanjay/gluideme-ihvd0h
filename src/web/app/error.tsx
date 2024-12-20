"use client";

import * as React from "react";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Button from "@/components/common/button";

// Version: ^18.2.0 - react
// Version: ^13.0.0 - next/navigation

/**
 * Props interface for the Error component
 */
interface ErrorProps {
  error: Error;
  reset: () => void;
}

/**
 * Error Page Component
 * 
 * A comprehensive error handling component that provides a user-friendly interface
 * for runtime errors. Implements WCAG 2.1 AA accessibility standards with proper
 * error announcements, keyboard navigation, and focus management.
 * 
 * @param {Error} error - Error object containing details about what went wrong
 * @param {() => void} reset - Function to reset the error boundary and retry rendering
 */
const Error: React.FC<ErrorProps> = ({ error, reset }) => {
  const router = useRouter();
  
  // Generate unique error tracking ID
  const errorId = React.useMemo(() => 
    `ERR-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    []
  );

  // Handle error logging and announcements
  useEffect(() => {
    // Log error to monitoring service with context
    console.error({
      errorId,
      error: error.message,
      stack: error.stack,
      timestamp: new Date().toISOString(),
      url: window.location.href,
    });

    // Announce error to screen readers
    const errorMessage = `An error occurred. ${error.message}`;
    const announcement = document.createElement("div");
    announcement.setAttribute("role", "alert");
    announcement.setAttribute("aria-live", "assertive");
    announcement.className = "sr-only";
    announcement.textContent = errorMessage;
    document.body.appendChild(announcement);

    // Cleanup announcement
    return () => {
      document.body.removeChild(announcement);
    };
  }, [error, errorId]);

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        router.push("/");
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [router]);

  // Focus management
  const mainHeadingRef = React.useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    mainHeadingRef.current?.focus();
  }, []);

  return (
    <main
      className="min-h-screen flex items-center justify-center px-4 py-16 bg-neutral-50 dark:bg-neutral-900"
      role="main"
      aria-labelledby="error-heading"
    >
      <div className="max-w-md w-full space-y-8 text-center">
        <div className="space-y-4">
          <h1
            id="error-heading"
            ref={mainHeadingRef}
            tabIndex={-1}
            className="text-2xl font-semibold text-neutral-900 dark:text-white"
          >
            Something went wrong
          </h1>
          
          <p className="text-neutral-600 dark:text-neutral-300">
            We apologize for the inconvenience. An unexpected error has occurred.
          </p>

          {process.env.NODE_ENV === "development" && (
            <div className="mt-4 p-4 bg-neutral-100 dark:bg-neutral-800 rounded-md text-left">
              <p className="text-sm font-mono text-neutral-700 dark:text-neutral-200">
                {error.message}
              </p>
            </div>
          )}

          <p className="text-sm text-neutral-500 dark:text-neutral-400">
            Error ID: {errorId}
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button
            onClick={reset}
            variant="primary"
            aria-label="Try again"
            className="w-full sm:w-auto"
          >
            Try again
          </Button>
          
          <Button
            onClick={() => router.push("/")}
            variant="outline"
            aria-label="Return to home page"
            className="w-full sm:w-auto"
          >
            Return to home
          </Button>
        </div>

        <p className="text-sm text-neutral-500 dark:text-neutral-400">
          If this problem persists, please contact support with the Error ID above.
        </p>
      </div>
    </main>
  );
};

export default Error;