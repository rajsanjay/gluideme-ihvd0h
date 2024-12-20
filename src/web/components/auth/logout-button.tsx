"use client";

import React, { useState, useCallback } from 'react'; // v18.2.0
import { useAuth } from '../../hooks/useAuth';
import Button from '../common/button';

/**
 * Props interface for LogoutButton component
 * Includes styling variants and callback handlers
 */
export interface LogoutButtonProps {
  /** Visual style variant of the button */
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  /** Size variant of the button */
  size?: 'sm' | 'md' | 'lg';
  /** Additional CSS classes for custom styling */
  className?: string;
  /** Accessible label for screen readers */
  ariaLabel?: string;
  /** Callback function called after successful logout */
  onLogoutSuccess?: () => void;
  /** Callback function called when logout fails */
  onLogoutError?: (error: Error) => void;
}

/**
 * LogoutButton Component
 * 
 * A reusable, accessible button component that handles user logout functionality
 * with loading states and error handling. Implements WCAG 2.1 AA compliance
 * and proper token cleanup.
 * 
 * @example
 * ```tsx
 * // Basic usage
 * <LogoutButton />
 * 
 * // Custom styling with callbacks
 * <LogoutButton 
 *   variant="outline"
 *   size="lg"
 *   onLogoutSuccess={() => router.push('/login')}
 *   onLogoutError={(error) => console.error(error)}
 * />
 * ```
 */
const LogoutButton: React.FC<LogoutButtonProps> = ({
  variant = 'primary',
  size = 'md',
  className,
  ariaLabel = 'Logout',
  onLogoutSuccess,
  onLogoutError,
}) => {
  // Get logout function from auth context
  const { logout } = useAuth();
  
  // Local loading state
  const [isLoading, setIsLoading] = useState(false);

  /**
   * Handles the logout process with loading state and error handling
   * Ensures proper cleanup of auth tokens and state
   */
  const handleLogout = useCallback(async () => {
    setIsLoading(true);
    
    try {
      await logout();
      
      // Clear any sensitive data from storage
      localStorage.removeItem('lastLogin');
      sessionStorage.clear();
      
      // Call success callback if provided
      onLogoutSuccess?.();
    } catch (error) {
      // Handle logout errors
      console.error('Logout failed:', error);
      
      // Call error callback if provided
      if (error instanceof Error) {
        onLogoutError?.(error);
      }
    } finally {
      setIsLoading(false);
    }
  }, [logout, onLogoutSuccess, onLogoutError]);

  return (
    <Button
      variant={variant}
      size={size}
      className={className}
      onClick={handleLogout}
      isLoading={isLoading}
      ariaLabel={ariaLabel}
      // Additional ARIA attributes for accessibility
      aria-busy={isLoading}
      aria-live="polite"
      data-testid="logout-button"
    >
      {isLoading ? 'Logging out...' : 'Logout'}
    </Button>
  );
};

// Set display name for dev tools
LogoutButton.displayName = 'LogoutButton';

export default LogoutButton;