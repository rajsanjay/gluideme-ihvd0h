/**
 * PostCSS Configuration
 * Version: 1.0.0
 * 
 * This configuration file sets up the PostCSS processing pipeline for the Transfer Requirements
 * Management System, implementing comprehensive CSS transformations for production-grade styling.
 * 
 * Plugin Versions:
 * - tailwindcss: ^3.3.0
 * - autoprefixer: ^10.4.0
 * - postcss-preset-env: ^8.0.0
 * - cssnano: ^6.0.0
 * - postcss-rtl: ^2.0.0
 */

module.exports = {
  plugins: [
    // Process Tailwind CSS directives and utilities
    require('tailwindcss'),

    // Add vendor prefixes for cross-browser compatibility
    require('autoprefixer'),

    // Convert modern CSS features to browser-compatible syntax
    require('postcss-preset-env')({
      stage: 2, // Use stage 2 features for broader browser support
      features: {
        'custom-properties': true, // Enable CSS variables
        'nesting-rules': true, // Enable CSS nesting
        'custom-media-queries': true, // Enable custom media queries
        'gap-properties': true, // Enable gap properties for flexbox/grid
        'logical-properties-and-values': true, // Enable logical properties for RTL support
      },
      autoprefixer: {
        flexbox: 'no-2009', // Modern flexbox support only
        grid: 'autoplace', // Enable grid autoplacement
      },
      preserve: false, // Remove original syntax after processing
    }),

    // Add RTL support for internationalization
    require('postcss-rtl')({
      safeBothPrefix: true, // Enable safe prefixing for both LTR and RTL
      ignorePseudoClasses: ['hover', 'active', 'focus'], // Preserve directional styles for states
    }),

    // Production-only optimizations
    ...process.env.NODE_ENV === 'production' ? [
      require('cssnano')({
        preset: [
          'advanced',
          {
            discardComments: {
              removeAll: true, // Remove all comments in production
            },
            reduceIdents: false, // Preserve custom identifiers
            zindex: false, // Preserve z-index values
            mergeIdents: false, // Preserve separate identifiers
            minifyFontValues: {
              removeQuotes: false, // Preserve font name quotes
            },
          },
        ],
      }),
    ] : [],
  ],

  // Source map configuration based on environment
  sourceMap: process.env.NODE_ENV !== 'production',
}