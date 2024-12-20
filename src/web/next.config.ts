/**
 * @fileoverview Next.js configuration with comprehensive security and performance optimizations
 * @version 1.0.0
 * 
 * This configuration implements enterprise-grade security headers, performance optimizations,
 * and AWS Amplify deployment settings for the Transfer Requirements Management System.
 */

import type { NextConfig } from 'next';
import { API_CONFIG } from './config/constants';
import crypto from 'crypto';

/**
 * Enhances Next.js configuration with comprehensive security headers
 * @param config - Base Next.js configuration
 * @returns Enhanced configuration with security headers
 */
const withSecurityHeaders = (config: NextConfig): NextConfig => {
  const nonce = crypto.randomBytes(16).toString('base64');
  
  return {
    ...config,
    headers: async () => [
      {
        source: '/:path*',
        headers: [
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              `script-src 'self' 'nonce-${nonce}'`,
              `style-src 'self' 'nonce-${nonce}'`,
              "img-src 'self' *.amazonaws.com data:",
              "connect-src 'self' *.amazonaws.com",
              "font-src 'self'",
              "object-src 'none'",
              "base-uri 'self'",
              "form-action 'self'",
              "frame-ancestors 'none'",
              `report-uri ${process.env.NEXT_PUBLIC_CSP_REPORT_URI}`
            ].join('; ')
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload'
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin'
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=()'
          },
          {
            key: 'Report-To',
            value: JSON.stringify({
              group: 'csp-endpoint',
              max_age: 10886400,
              endpoints: [{ url: '/api/csp-report' }]
            })
          }
        ]
      }
    ]
  };
};

/**
 * Main Next.js configuration object
 * Implements comprehensive build and runtime optimizations
 */
const config: NextConfig = {
  // Enable React strict mode for enhanced development checks
  reactStrictMode: true,

  // Use SWC minification for faster builds
  swcMinify: true,

  // Generate standalone output for AWS deployment
  output: 'standalone',

  // Disable X-Powered-By header for security
  poweredByHeader: false,

  // Experimental features for enhanced performance
  experimental: {
    // Enable concurrent features for improved rendering
    concurrentFeatures: true,
    // Enable server components for optimal performance
    serverComponents: true,
    // Optimize CSS for reduced bundle size
    optimizeCss: true,
    // Enable scroll restoration for better UX
    scrollRestoration: true,
    // Enable optimistic client cache
    optimisticClientCache: true
  },

  // Image optimization configuration
  images: {
    domains: ['*.amazonaws.com'],
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    minimumCacheTTL: 60
  },

  // API route rewrites
  rewrites: async () => [
    {
      source: '/api/:path*',
      destination: `${API_CONFIG.BASE_URL}/api/:path*`
    }
  ],

  // Webpack configuration for optimizations
  webpack: (config, { dev, isServer }) => {
    // Enable bundle analysis in production
    if (!dev && !isServer) {
      const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');
      config.plugins.push(
        new BundleAnalyzerPlugin({
          analyzerMode: 'static',
          reportFilename: './bundle-analysis.html'
        })
      );
    }

    // Remove console logs in production except errors and warnings
    if (!dev) {
      config.optimization.minimize = true;
      config.optimization.minimizer.push(
        new (require('terser-webpack-plugin'))({
          terserOptions: {
            compress: {
              drop_console: true,
              drop_debugger: true,
              pure_funcs: ['console.log'],
              keep_fnames: false,
              keep_classnames: false
            }
          }
        })
      );
    }

    return config;
  },

  // Environment configuration
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_APP_ENV: process.env.NEXT_PUBLIC_APP_ENV,
    NEXT_PUBLIC_CSP_REPORT_URI: process.env.NEXT_PUBLIC_CSP_REPORT_URI
  },

  // CDN configuration for AWS CloudFront
  async headers() {
    return [
      {
        source: '/_next/static/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable'
          }
        ]
      }
    ];
  }
};

// Apply security headers and export final configuration
export default withSecurityHeaders(config);