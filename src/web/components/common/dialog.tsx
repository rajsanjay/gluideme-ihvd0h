"use client";

import * as React from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { cn } from "class-variance-authority";
import { Button } from "./button";

// Version: ^1.0.4 - @radix-ui/react-dialog
// Version: ^0.7.0 - class-variance-authority
// Version: ^18.2.0 - react

/**
 * Defines dialog style variants using class-variance-authority
 * Supports multiple sizes, themes, and animations
 */
export const dialogVariants = cn(
  // Base styles
  "fixed z-50 gap-4 bg-background p-6 shadow-lg duration-200",
  "data-[state=open]:animate-in data-[state=closed]:animate-out",
  "data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
  "data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95",
  "data-[state=closed]:slide-out-to-left-1/2 data-[state=open]:slide-in-from-left-1/2",
  "data-[state=closed]:slide-out-to-top-[48%] data-[state=open]:slide-in-from-top-[48%]",
  {
    variants: {
      size: {
        sm: "max-w-sm",
        md: "max-w-md",
        lg: "max-w-lg",
      },
      theme: {
        light: "bg-white text-gray-900",
        dark: "bg-gray-800 text-white",
      },
    },
    defaultVariants: {
      size: "md",
      theme: "light",
    },
  }
);

/**
 * Custom hook for managing focus trap within dialog
 */
function useDialogFocus(isOpen: boolean, initialFocus?: React.RefObject<HTMLElement>) {
  const dialogRef = React.useRef<HTMLDivElement>(null);
  const lastActiveElement = React.useRef<HTMLElement | null>(null);

  React.useEffect(() => {
    if (isOpen) {
      lastActiveElement.current = document.activeElement as HTMLElement;
      if (initialFocus?.current) {
        initialFocus.current.focus();
      } else if (dialogRef.current) {
        const firstFocusable = dialogRef.current.querySelector<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        firstFocusable?.focus();
      }
    } else {
      lastActiveElement.current?.focus();
    }
  }, [isOpen, initialFocus]);

  const handleKeyDown = React.useCallback(
    (e: KeyboardEvent) => {
      if (!isOpen || !dialogRef.current) return;

      const focusableElements = dialogRef.current.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      const firstFocusable = focusableElements[0];
      const lastFocusable = focusableElements[focusableElements.length - 1];

      if (e.key === "Tab") {
        if (e.shiftKey && document.activeElement === firstFocusable) {
          e.preventDefault();
          lastFocusable.focus();
        } else if (!e.shiftKey && document.activeElement === lastFocusable) {
          e.preventDefault();
          firstFocusable.focus();
        }
      }
    },
    [isOpen]
  );

  React.useEffect(() => {
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  return dialogRef;
}

/**
 * Props interface for Dialog component
 */
export interface DialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  size?: "sm" | "md" | "lg";
  title: string;
  description?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  className?: string;
  closeOnOutsideClick?: boolean;
  closeOnEscape?: boolean;
  initialFocus?: React.RefObject<HTMLElement>;
  onClose?: () => void;
  theme?: "light" | "dark";
}

/**
 * Dialog Component
 * 
 * A highly accessible modal dialog component that implements the design system's
 * dialog patterns. Supports multiple sizes, themes, and customizable sections.
 * Fully compliant with WCAG 2.1 AA standards.
 * 
 * @example
 * ```tsx
 * <Dialog
 *   isOpen={isOpen}
 *   onOpenChange={setIsOpen}
 *   title="Confirm Action"
 *   description="Are you sure you want to proceed?"
 *   footer={
 *     <>
 *       <Button variant="ghost" onClick={onCancel}>Cancel</Button>
 *       <Button variant="primary" onClick={onConfirm}>Confirm</Button>
 *     </>
 *   }
 * >
 *   <p>This action cannot be undone.</p>
 * </Dialog>
 * ```
 */
export const Dialog: React.FC<DialogProps> = ({
  isOpen,
  onOpenChange,
  size = "md",
  title,
  description,
  children,
  footer,
  className,
  closeOnOutsideClick = true,
  closeOnEscape = true,
  initialFocus,
  onClose,
  theme = "light",
}) => {
  const dialogRef = useDialogFocus(isOpen, initialFocus);

  const handleClose = React.useCallback(() => {
    onClose?.();
    onOpenChange(false);
  }, [onClose, onOpenChange]);

  return (
    <DialogPrimitive.Root
      open={isOpen}
      onOpenChange={closeOnOutsideClick ? onOpenChange : undefined}
    >
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay
          className={cn(
            "fixed inset-0 z-40 bg-black/50",
            "data-[state=open]:animate-in data-[state=closed]:animate-out",
            "data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0"
          )}
        />
        <DialogPrimitive.Content
          ref={dialogRef}
          onEscapeKeyDown={(e) => {
            if (!closeOnEscape) {
              e.preventDefault();
            }
          }}
          className={cn(
            dialogVariants({ size, theme }),
            "fixed left-[50%] top-[50%] z-50 translate-x-[-50%] translate-y-[-50%]",
            className
          )}
        >
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <DialogPrimitive.Title className="text-lg font-semibold leading-none">
                {title}
              </DialogPrimitive.Title>
              {description && (
                <DialogPrimitive.Description className="text-sm text-gray-500 dark:text-gray-400">
                  {description}
                </DialogPrimitive.Description>
              )}
            </div>

            <div className="flex-1">{children}</div>

            {footer && (
              <div className="flex justify-end gap-3 pt-4 mt-4 border-t border-gray-200 dark:border-gray-700">
                {footer}
              </div>
            )}

            <DialogPrimitive.Close
              className={cn(
                "absolute right-4 top-4 rounded-sm opacity-70 transition-opacity",
                "hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-offset-2",
                "disabled:pointer-events-none",
                theme === "light"
                  ? "focus:ring-gray-400"
                  : "focus:ring-gray-600"
              )}
              onClick={handleClose}
            >
              <span className="sr-only">Close</span>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="w-4 h-4"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M18 6L6 18M6 6l12 12" />
              </svg>
            </DialogPrimitive.Close>
          </div>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
};

Dialog.displayName = "Dialog";

export default Dialog;