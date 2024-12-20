import type { Config } from '@jest/types'; // v29.0.0
import { resolve } from 'path';

/**
 * Creates and exports the comprehensive Jest configuration for the frontend testing environment.
 * Implements advanced testing features including:
 * - TypeScript and React component testing support
 * - Comprehensive code coverage requirements
 * - Asset and module mocking
 * - Accessibility testing setup
 * - Performance optimization settings
 */
const createJestConfig = (): Config.InitialOptions => ({
  // Test environment configuration
  testEnvironment: 'jsdom',
  roots: ['<rootDir>/src'],
  
  // Test file patterns and locations
  testMatch: [
    '**/__tests__/**/*.test.ts?(x)',
    '**/?(*.)+(spec|test).ts?(x)'
  ],
  testPathIgnorePatterns: [
    '/node_modules/',
    '/dist/'
  ],

  // Setup and configuration files
  setupFilesAfterEnv: [
    '<rootDir>/__tests__/setup.ts'
  ],

  // Module resolution and path mapping
  moduleNameMapper: {
    // Path aliases
    '^@/(.*)$': '<rootDir>/src/$1',
    
    // Asset mocks
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    '\\.(jpg|jpeg|png|gif|svg|eot|otf|webp|ttf|woff|woff2|mp4|webm|wav|mp3|m4a|aac|oga)$': 
      '<rootDir>/__mocks__/fileMock.js'
  },

  // File extensions to process
  moduleFileExtensions: [
    'ts',
    'tsx',
    'js',
    'jsx',
    'json',
    'node'
  ],

  // TypeScript and JavaScript transformation
  transform: {
    '^.+\\.tsx?$': [
      'ts-jest',
      {
        tsconfig: resolve(__dirname, './tsconfig.json')
      }
    ],
    '^.+\\.jsx?$': 'babel-jest'
  },

  // Code coverage configuration
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/types/**/*',
    '!src/**/*.stories.{ts,tsx}',
    '!src/**/__mocks__/**',
    '!src/**/__tests__/**'
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  },
  coverageReporters: [
    'text',
    'html',
    'lcov',
    'cobertura'
  ],

  // Test execution settings
  testTimeout: 10000,
  maxWorkers: '50%',
  
  // Mock behavior configuration
  clearMocks: true,
  restoreMocks: true,
  resetMocks: true,

  // Watch mode plugins
  watchPlugins: [
    'jest-watch-typeahead/filename',
    'jest-watch-typeahead/testname'
  ],

  // Global settings
  globals: {
    'ts-jest': {
      isolatedModules: true,
      diagnostics: {
        warnOnly: true
      }
    },
    TEST_ENV: process.env.NODE_ENV === 'test'
  },

  // Snapshot settings
  snapshotSerializers: [
    'jest-serializer-html'
  ],
  
  // Error handling and reporting
  errorOnDeprecated: true,
  verbose: true
});

// Export the configuration
const config = createJestConfig();
export default config;