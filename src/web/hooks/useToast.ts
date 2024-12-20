/**
 * @fileoverview Custom React hook for managing accessible toast notifications
 * Provides a simple interface for displaying, updating and dismissing toasts
 * with built-in accessibility and RTL support
 * @version 1.0.0
 */

import { useContext, useCallback, useRef } from 'react'; // v18.2.0
import { ToastContext } from '../providers/toast-provider';
import type { LoadingState } from '../types/common';

/**
 * Interface for toast notification options
 */
export interface ToastOptions {
  /** Message content to display */
  message: string;
  /** Type of notification */
  type?: 'success' | 'error' | 'warning' | 'info';
  /** Duration in milliseconds (0 for no auto-dismiss) */
  duration?: number;
  /** Position on screen */
  position?: 'top' | 'bottom' | 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  /** Accessibility label for screen readers */
  ariaLabel?: string;
  /** Enable RTL text direction */
  rtl?: boolean;
  /** ARIA role override */
  role?: 'status' | 'alert';
  /** Keep toast visible during route changes */
  preserveOnRouteChange?: boolean;
}

/**
 * Custom hook for managing toast notifications with accessibility support
 * @returns Object containing toast management functions
 */
export const useToast = () => {
  // Get toast context
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }

  const { showToast: contextShow, hideToast: contextHide, toasts } = context;

  // Track loading state for animations
  const loadingState = useRef<LoadingState>('idle');
  
  // Track animation frames for cleanup
  const animationFrame = useRef<number>();

  /**
   * Shows a toast notification with enhanced accessibility
   */
  const show = useCallback((options: ToastOptions) => {
    // Cancel any pending animations
    if (animationFrame.current) {
      cancelAnimationFrame(animationFrame.current);
    }

    // Set appropriate ARIA role based on type
    const role = options.role || (options.type === 'error' ? 'alert' : 'status');
    
    // Set appropriate ARIA live region based on type
    const ariaLive = options.type === 'error' ? 'assertive' : 'polite';

    // Handle RTL text direction
    const rtlClass = options.rtl ? 'direction-rtl' : undefined;

    // Prepare enhanced options
    const enhancedOptions = {
      ...options,
      role,
      ariaLive,
      className: rtlClass,
      // Ensure message is screen-reader friendly
      ariaLabel: options.ariaLabel || options.message
    };

    // Show toast with smooth animation
    loadingState.current = 'loading';
    animationFrame.current = requestAnimationFrame(() => {
      contextShow(enhancedOptions);
    });

    // Announce to screen readers if not an error (errors use aria-live)
    if (options.type !== 'error') {
      const announcement = document.createElement('div');
      announcement.setAttribute('role', 'status');
      announcement.setAttribute('aria-live', 'polite');
      announcement.textContent = options.message;
      document.body.appendChild(announcement);
      setTimeout(() => announcement.remove(), 1000);
    }
  }, [contextShow]);

  /**
   * Hides the current toast notification
   */
  const hide = useCallback(() => {
    // Cancel any pending animations
    if (animationFrame.current) {
      cancelAnimationFrame(animationFrame.current);
    }

    // Reset loading state
    loadingState.current = 'idle';

    // Hide toast with smooth animation
    contextHide();
  }, [contextHide]);

  /**
   * Updates the content of the current toast
   */
  const update = useCallback((options: Partial<ToastOptions>) => {
    // Hide current toast
    hide();
    
    // Show updated toast
    show({
      ...options,
      // Preserve existing options if not provided
      message: options.message || '',
      type: options.type || 'info',
      duration: options.duration || 5000,
      position: options.position || 'top-right'
    });
  }, [show, hide]);

  return {
    /**
     * Display a new toast notification
     */
    show,

    /**
     * Hide the current toast notification
     */
    hide,

    /**
     * Update the current toast notification
     */
    update,

    /**
     * Check if a toast is currently visible
     */
    isVisible: toasts.length > 0
  };
};

/**
 * Example usage:
 * 
 * const { show, hide, update, isVisible } = useToast();
 * 
 * // Show a success toast
 * show({
 *   message: "Operation successful!",
 *   type: "success",
 *   duration: 5000,
 *   position: "top-right"
 * });
 * 
 * // Show an error toast with RTL support
 * show({
 *   message: "خطأ في العملية",
 *   type: "error",
 *   rtl: true,
 *   ariaLabel: "Operation error"
 * });
 * 
 * // Update current toast
 * update({
 *   message: "Updated message",
 *   type: "info"
 * });
 * 
 * // Hide current toast
 * hide();
 */