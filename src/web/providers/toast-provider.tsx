/**
 * @fileoverview Toast notification provider with enhanced accessibility and theme support
 * Manages global toast state and provides methods for displaying notifications
 * @version 1.0.0
 */

import React, { createContext, useContext, useState, useCallback, useRef, useEffect } from 'react'; // v18.2.0
import { useMediaQuery } from '@react-hook/media-query'; // v1.1.1
import { useTheme } from '@shadcn/ui'; // latest
import { Toast } from '@/components/common/toast';
import type { LoadingState } from '@/types/common';

/**
 * Interface for toast notification options
 */
interface ToastOptions {
  message: string | React.ReactNode;
  type?: 'success' | 'error' | 'warning' | 'info';
  duration?: number;
  position?: 'top' | 'bottom' | 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  theme?: 'light' | 'dark';
  isRTL?: boolean;
}

/**
 * Interface for toast state management
 */
interface ToastState {
  id: string;
  options: ToastOptions;
  timerId?: number;
}

/**
 * Interface for toast context
 */
interface ToastContextType {
  showToast: (options: ToastOptions) => void;
  hideToast: (id: string) => void;
  toasts: ToastState[];
}

// Create context with default values
const ToastContext = createContext<ToastContextType>({
  showToast: () => undefined,
  hideToast: () => undefined,
  toasts: [],
});

/**
 * Maximum number of simultaneous toasts
 */
const MAX_TOASTS = 3;

/**
 * Default duration for toasts in milliseconds
 */
const DEFAULT_DURATION = 5000;

/**
 * Toast Provider component that manages global toast state
 */
export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // State for managing active toasts
  const [toasts, setToasts] = useState<ToastState[]>([]);
  
  // Theme context for proper styling
  const { theme } = useTheme();
  
  // Check for reduced motion preference
  const prefersReducedMotion = useMediaQuery('(prefers-reduced-motion: reduce)');
  
  // Ref for managing toast IDs
  const toastIdCounter = useRef(0);
  
  // Ref for tracking active timers
  const timerRefs = useRef<Map<string, number>>(new Map());

  /**
   * Cleanup function for removing toast timers
   */
  const cleanupTimer = useCallback((id: string) => {
    const timerId = timerRefs.current.get(id);
    if (timerId) {
      window.clearTimeout(timerId);
      timerRefs.current.delete(id);
    }
  }, []);

  /**
   * Function to show a new toast notification
   */
  const showToast = useCallback((options: ToastOptions) => {
    const id = `toast-${++toastIdCounter.current}`;
    
    // Apply defaults and theme
    const toastOptions = {
      ...options,
      duration: options.duration || DEFAULT_DURATION,
      theme: options.theme || theme,
      position: options.position || 'top-right'
    };

    setToasts(currentToasts => {
      // Remove oldest toast if at max capacity
      const updatedToasts = currentToasts.length >= MAX_TOASTS
        ? currentToasts.slice(1)
        : currentToasts;

      return [...updatedToasts, { id, options: toastOptions }];
    });

    // Set auto-dismiss timer unless duration is 0
    if (toastOptions.duration > 0) {
      const timerId = window.setTimeout(() => {
        hideToast(id);
      }, toastOptions.duration);
      
      timerRefs.current.set(id, timerId);
    }

    // Announce toast for screen readers
    const announcement = document.createElement('div');
    announcement.setAttribute('role', 'status');
    announcement.setAttribute('aria-live', options.type === 'error' ? 'assertive' : 'polite');
    announcement.textContent = typeof options.message === 'string' ? options.message : 'Notification';
    document.body.appendChild(announcement);
    setTimeout(() => announcement.remove(), 1000);

  }, [theme]);

  /**
   * Function to hide a specific toast
   */
  const hideToast = useCallback((id: string) => {
    cleanupTimer(id);
    setToasts(currentToasts => currentToasts.filter(toast => toast.id !== id));
  }, [cleanupTimer]);

  /**
   * Cleanup effect for removing timers on unmount
   */
  useEffect(() => {
    return () => {
      timerRefs.current.forEach((timerId) => {
        window.clearTimeout(timerId);
      });
      timerRefs.current.clear();
    };
  }, []);

  return (
    <ToastContext.Provider value={{ showToast, hideToast, toasts }}>
      {children}
      {toasts.map(({ id, options }) => (
        <Toast
          key={id}
          message={options.message}
          type={options.type}
          position={options.position}
          duration={prefersReducedMotion ? 0 : options.duration}
          onClose={() => hideToast(id)}
          className={options.isRTL ? 'direction-rtl' : undefined}
          // Additional accessibility attributes
          role={options.type === 'error' ? 'alert' : 'status'}
          aria-live={options.type === 'error' ? 'assertive' : 'polite'}
        />
      ))}
    </ToastContext.Provider>
  );
};

/**
 * Custom hook for using toast functionality
 */
export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

// Export context for testing purposes
export { ToastContext };