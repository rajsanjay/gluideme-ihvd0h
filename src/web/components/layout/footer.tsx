"use client";

import * as React from "react";
// Version: ^18.2.0 - react
import { cn } from "class-variance-authority";
// Version: ^0.7.0 - class-variance-authority
import { Button } from "../common/button";

/**
 * Interface for footer link configuration
 */
interface FooterLink {
  label: string;
  href: string;
  ariaLabel?: string;
}

/**
 * Interface for social media link configuration
 */
interface SocialLink extends FooterLink {
  icon: React.ReactNode;
}

/**
 * Theme configuration interface for footer styling
 */
interface FooterTheme {
  backgroundColor?: string;
  textColor?: string;
  linkColor?: string;
}

/**
 * Content configuration interface for footer sections
 */
interface FooterContent {
  logo: React.ReactNode;
  navigationLinks: FooterLink[];
  legalLinks: FooterLink[];
  socialLinks: SocialLink[];
}

/**
 * Props interface for Footer component
 */
interface FooterProps {
  className?: string;
  theme?: FooterTheme;
  content?: FooterContent;
  navigationAriaLabel?: string;
}

/**
 * Get current year for copyright notice
 * Memoized to prevent unnecessary recalculations
 */
const getCurrentYear = (): number => {
  return new Date().getFullYear();
};

/**
 * Footer Component
 * 
 * A responsive, accessible footer component that implements the design system's
 * footer layout patterns. Supports customizable content, theming, and follows
 * WCAG 2.1 AA accessibility guidelines.
 * 
 * @param props FooterProps
 */
const Footer: React.FC<FooterProps> = ({
  className,
  theme = {},
  content,
  navigationAriaLabel = "Footer Navigation",
}) => {
  const year = React.useMemo(() => getCurrentYear(), []);

  // Default theme values
  const {
    backgroundColor = "bg-neutral-900 dark:bg-neutral-950",
    textColor = "text-neutral-200 dark:text-neutral-300",
    linkColor = "text-neutral-300 hover:text-white dark:text-neutral-400 dark:hover:text-white",
  } = theme;

  return (
    <footer
      className={cn(
        "w-full",
        backgroundColor,
        textColor,
        "py-12 lg:py-16",
        className
      )}
      role="contentinfo"
    >
      <div className="container mx-auto px-4 md:px-6">
        {/* Main footer content */}
        <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-4">
          {/* Logo and company info section */}
          <div className="flex flex-col space-y-4">
            {content?.logo && (
              <div className="flex items-center">
                {content.logo}
              </div>
            )}
            <p className="text-sm">
              Transfer Requirements Management System for California higher education institutions.
            </p>
          </div>

          {/* Navigation links section */}
          <nav
            className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:col-span-2"
            aria-label={navigationAriaLabel}
          >
            {content?.navigationLinks?.map((link, index) => (
              <a
                key={`nav-link-${index}`}
                href={link.href}
                className={cn(
                  "text-sm transition-colors duration-200",
                  linkColor
                )}
                aria-label={link.ariaLabel || link.label}
              >
                {link.label}
              </a>
            ))}
          </nav>

          {/* Social links section */}
          <div className="flex flex-col space-y-4">
            <h3 className="text-sm font-semibold">Connect With Us</h3>
            <div className="flex space-x-4">
              {content?.socialLinks?.map((social, index) => (
                <Button
                  key={`social-link-${index}`}
                  variant="ghost"
                  size="sm"
                  aria-label={social.ariaLabel || social.label}
                  onClick={() => window.open(social.href, '_blank')}
                >
                  {social.icon}
                </Button>
              ))}
            </div>
          </div>
        </div>

        {/* Bottom bar with copyright and legal links */}
        <div className="mt-12 flex flex-col items-center space-y-4 border-t border-neutral-800 pt-8 md:flex-row md:justify-between md:space-y-0">
          <p className="text-sm">
            © {year} Transfer Requirements Management System. All rights reserved.
          </p>
          
          <div className="flex space-x-6">
            {content?.legalLinks?.map((link, index) => (
              <a
                key={`legal-link-${index}`}
                href={link.href}
                className={cn(
                  "text-sm transition-colors duration-200",
                  linkColor
                )}
                aria-label={link.ariaLabel || link.label}
              >
                {link.label}
              </a>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
};

// Set display name for dev tools
Footer.displayName = "Footer";

export default Footer;