"use client";

import * as React from "react";
import LoadingSpinner from "../../components/common/loading-spinner";

/**
 * Loading Component
 * 
 * A full-page loading component used by Next.js during page transitions and data fetching.
 * Implements design system specifications with enhanced accessibility features and
 * performance optimizations.
 * 
 * Features:
 * - Centered full-screen loading indicator
 * - ARIA-compliant accessibility
 * - Reduced motion support
 * - Performance optimized animations
 * - Fallback content for extended loading states
 */
const Loading: React.FC = () => {
  // Track loading duration for fallback message
  const [showFallback, setShowFallback] = React.useState(false);

  // Show fallback message after 10 seconds
  React.useEffect(() => {
    const timer = setTimeout(() => setShowFallback(true), 10000);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div 
      className="min-h-screen flex items-center justify-center bg-background will-change-transform"
      role="status"
      aria-live="polite"
    >
      <div className="flex flex-col items-center gap-4">
        <LoadingSpinner 
          size="lg"
          color="primary"
          className="text-primary"
          aria-label="Loading page content"
        />
        
        {/* Fallback message for extended loading times */}
        {showFallback && (
          <p className="text-muted-foreground text-sm animate-fade-in">
            This is taking longer than expected. Please wait...
          </p>
        )}
      </div>
    </div>
  );
};

export default Loading;