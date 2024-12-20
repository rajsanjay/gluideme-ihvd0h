/**
 * @fileoverview Production-ready toast notification component built on Radix UI
 * Provides accessible, customizable notifications with support for multiple types and positions
 * @version 1.0.0
 */

import * as React from 'react';
import * as ToastPrimitives from '@radix-ui/react-toast'; // v1.1.3
import { cn } from '@/lib/utils';
import { LoadingState } from '@/types/common';

/**
 * Available toast notification types
 */
export type ToastType = 'success' | 'error' | 'warning' | 'info';

/**
 * Available toast notification positions
 */
export type ToastPosition = 
  | 'top'
  | 'bottom'
  | 'top-right'
  | 'top-left'
  | 'bottom-right'
  | 'bottom-left';

/**
 * Props interface for the Toast component
 */
export interface ToastProps extends React.ComponentPropsWithoutRef<typeof ToastPrimitives.Root> {
  message: string;
  type?: ToastType;
  duration?: number;
  position?: ToastPosition;
  onClose?: () => void;
  title?: string;
  className?: string;
}

/**
 * Props interface for the ToastViewport component
 */
export interface ToastViewportProps extends React.ComponentPropsWithoutRef<typeof ToastPrimitives.Viewport> {
  className?: string;
  hotkey?: string[];
  label?: string;
}

/**
 * Mapping of toast types to their corresponding styles
 */
const toastTypeStyles: Record<ToastType, string> = {
  success: 'bg-green-50 border-green-500 text-green-800',
  error: 'bg-red-50 border-red-500 text-red-800',
  warning: 'bg-yellow-50 border-yellow-500 text-yellow-800',
  info: 'bg-blue-50 border-blue-500 text-blue-800'
};

/**
 * Mapping of toast positions to their corresponding styles
 */
const toastPositionStyles: Record<ToastPosition, string> = {
  'top': 'top-0 left-1/2 -translate-x-1/2',
  'bottom': 'bottom-0 left-1/2 -translate-x-1/2',
  'top-right': 'top-0 right-0',
  'top-left': 'top-0 left-0',
  'bottom-right': 'bottom-0 right-0',
  'bottom-left': 'bottom-0 left-0'
};

/**
 * Main Toast component that renders an accessible notification message
 */
export const Toast = React.forwardRef<HTMLDivElement, ToastProps>(
  ({ className, message, type = 'info', duration = 5000, position = 'top-right', onClose, title, ...props }, ref) => {
    // Track loading state for animations
    const [loadingState, setLoadingState] = React.useState<LoadingState>('idle');

    // Handle animation frame for smooth transitions
    React.useEffect(() => {
      const frame = requestAnimationFrame(() => setLoadingState('loading'));
      return () => cancelAnimationFrame(frame);
    }, []);

    // Combine class names based on type and position
    const toastClasses = cn(
      'fixed z-50 flex items-center p-4 mb-4 border rounded-lg shadow-lg',
      'transition-all duration-300 ease-in-out',
      toastTypeStyles[type],
      toastPositionStyles[position],
      loadingState === 'loading' ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2',
      className
    );

    return (
      <ToastPrimitives.Root
        ref={ref}
        className={toastClasses}
        duration={duration}
        onOpenChange={(open) => {
          if (!open && onClose) {
            onClose();
          }
        }}
        {...props}
        // Set appropriate ARIA attributes based on toast type
        role={type === 'error' ? 'alert' : 'status'}
        aria-live={type === 'error' ? 'assertive' : 'polite'}
      >
        <div className="flex flex-col gap-1">
          {title && (
            <ToastPrimitives.Title className="text-sm font-semibold">
              {title}
            </ToastPrimitives.Title>
          )}
          <ToastPrimitives.Description className="text-sm">
            {message}
          </ToastPrimitives.Description>
        </div>
      </ToastPrimitives.Root>
    );
  }
);

Toast.displayName = 'Toast';

/**
 * ToastViewport component that defines the container for toast notifications
 */
export const ToastViewport = React.forwardRef<HTMLDivElement, ToastViewportProps>(
  ({ className, ...props }, ref) => {
    const viewportClasses = cn(
      'fixed flex flex-col gap-2 p-4 w-full sm:max-w-md',
      'outline-none',
      className
    );

    return (
      <ToastPrimitives.Viewport
        ref={ref}
        className={viewportClasses}
        // Set appropriate ARIA attributes for accessibility
        aria-label="Notifications"
        role="region"
        {...props}
      />
    );
  }
);

ToastViewport.displayName = 'ToastViewport';

/**
 * ToastProvider component that manages the toast notification context
 */
export const ToastProvider = ToastPrimitives.Provider;

/**
 * Example usage:
 * 
 * <ToastProvider>
 *   <Toast
 *     message="Operation successful!"
 *     type="success"
 *     position="top-right"
 *     duration={5000}
 *     onClose={() => console.log('Toast closed')}
 *   />
 *   <ToastViewport />
 * </ToastProvider>
 */