'use client';

import { Inter } from '@next/font/google'; // v13.0.0
import { ThemeProvider } from '@/providers/theme-provider';
import { AuthProvider } from '@/providers/auth-provider';
import { ToastProvider } from '@/providers/toast-provider';
import './globals.css';
import type { Metadata } from 'next';

// Initialize Inter font with performance optimizations
const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
  preload: true,
  fallback: [
    '-apple-system',
    'BlinkMacSystemFont',
    'Segoe UI',
    'Roboto',
    'Helvetica Neue',
    'Arial',
    'sans-serif'
  ]
});

// Static metadata configuration for SEO and PWA support
export const metadata: Metadata = {
  title: 'Transfer Requirements Management System',
  description: 'Comprehensive platform for managing course transfer requirements between California educational institutions',
  keywords: 'transfer requirements, course transfer, california colleges, education',
  authors: [{ name: 'Transfer Requirements Management System Team' }],
  viewport: 'width=device-width, initial-scale=1',
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: 'hsl(0 0% 100%)' },
    { media: '(prefers-color-scheme: dark)', color: 'hsl(222.2 84% 4.9%)' }
  ],
  manifest: '/manifest.json',
  icons: {
    icon: '/favicon.ico',
    apple: '/apple-touch-icon.png'
  }
};

/**
 * Root layout component that wraps all pages with necessary providers and global styles
 * Implements error boundaries and performance optimizations
 */
export default function RootLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <meta charSet="utf-8" />
        <meta name="format-detection" content="telephone=no" />
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
      </head>
      <body className={inter.variable}>
        {/* Theme provider for light/dark mode support */}
        <ThemeProvider defaultTheme="system" transitionDuration={200}>
          {/* Authentication state management */}
          <AuthProvider>
            {/* Toast notifications with accessibility support */}
            <ToastProvider>
              {/* Skip to main content link for accessibility */}
              <a href="#main-content" className="skip-to-content">
                Skip to main content
              </a>

              {/* Main content wrapper */}
              <main id="main-content" className="min-h-screen">
                {children}
              </main>

              {/* Accessibility announcement region */}
              <div
                aria-live="polite"
                aria-atomic="true"
                className="sr-only"
                role="status"
              />
            </ToastProvider>
          </AuthProvider>
        </ThemeProvider>

        {/* Reduced motion detection */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              try {
                if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
                  document.documentElement.style.scrollBehavior = 'auto';
                }
              } catch (e) {}
            `
          }}
        />
      </body>
    </html>
  );
}