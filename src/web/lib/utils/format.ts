/**
 * @fileoverview Comprehensive utility functions for formatting data with i18n and a11y support
 * @version 1.0.0
 */

import { DateRange } from '../../types/common';
import { formatNumber } from 'intl-number-format'; // v1.3.0

/**
 * Regular expression for validating course codes across institutions
 * Matches patterns like: CS 101, MATH 101A, PHYS 101
 */
export const COURSE_CODE_REGEX = /^[A-Z]{2,4}\s?\d{3}[A-Z]?$/i;

/**
 * Standard format for displaying course units
 */
export const UNIT_DISPLAY_FORMAT = '0.0 Units';

/**
 * Standard format for displaying percentages
 */
export const PERCENTAGE_FORMAT = '0.0%';

/**
 * Common institution name abbreviations and their full forms
 */
export const INSTITUTION_ABBREVIATIONS: Record<string, string> = {
  UC: 'University of California',
  CSU: 'California State University'
};

/**
 * Custom error class for format-related errors
 */
class FormatError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'FormatError';
  }
}

/**
 * Formats a course code according to institution-specific standards
 * @param code - Raw course code to format
 * @param institutionType - Optional institution type for specific formatting rules
 * @returns Formatted course code
 * @throws {FormatError} If the code is invalid
 */
export function formatCourseCode(code: string, institutionType?: string): string {
  if (!code?.trim()) {
    throw new FormatError('Course code cannot be empty');
  }

  // Normalize spacing and casing
  const normalizedCode = code.trim().toUpperCase();
  
  // Apply institution-specific formatting
  let formattedCode = normalizedCode;
  if (institutionType) {
    switch (institutionType.toUpperCase()) {
      case 'UC':
        // UC format: Ensure single space between department and number
        formattedCode = normalizedCode.replace(/\s+/g, ' ');
        break;
      case 'CSU':
        // CSU format: No space between department and number
        formattedCode = normalizedCode.replace(/\s+/g, '');
        break;
      default:
        // Default format: Single space between department and number
        formattedCode = normalizedCode.replace(/\s+/g, ' ');
    }
  }

  // Validate against pattern
  if (!COURSE_CODE_REGEX.test(formattedCode)) {
    throw new FormatError('Invalid course code format');
  }

  return formattedCode;
}

/**
 * Formats course units with locale support
 * @param units - Number of units to format
 * @param locale - Optional locale for formatting (defaults to user's locale)
 * @returns Formatted unit string
 * @throws {FormatError} If units is negative or invalid
 */
export function formatUnits(units: number, locale?: string): string {
  if (typeof units !== 'number' || units < 0) {
    throw new FormatError('Units must be a non-negative number');
  }

  try {
    const formattedNumber = formatNumber(units, {
      locale: locale || navigator.language,
      minimumFractionDigits: 1,
      maximumFractionDigits: 1
    });

    return `${formattedNumber} Units`;
  } catch (error) {
    throw new FormatError('Failed to format units');
  }
}

/**
 * Formats a decimal as a percentage with locale support
 * @param value - Decimal value to format as percentage (0-1)
 * @param locale - Optional locale for formatting
 * @returns Formatted percentage string
 * @throws {FormatError} If value is outside valid range
 */
export function formatPercentage(value: number, locale?: string): string {
  if (typeof value !== 'number' || value < 0 || value > 1) {
    throw new FormatError('Percentage value must be between 0 and 1');
  }

  try {
    return formatNumber(value, {
      locale: locale || navigator.language,
      style: 'percent',
      minimumFractionDigits: 1,
      maximumFractionDigits: 1
    });
  } catch (error) {
    throw new FormatError('Failed to format percentage');
  }
}

/**
 * Formats institution names with proper abbreviation handling
 * @param name - Institution name to format
 * @param locale - Optional locale for formatting
 * @returns Formatted institution name
 * @throws {FormatError} If name is invalid
 */
export function formatInstitutionName(name: string, locale?: string): string {
  if (!name?.trim()) {
    throw new FormatError('Institution name cannot be empty');
  }

  const trimmedName = name.trim();
  
  // Handle known abbreviations
  for (const [abbr, fullName] of Object.entries(INSTITUTION_ABBREVIATIONS)) {
    if (trimmedName.toUpperCase() === abbr) {
      return fullName;
    }
    // Handle campus-specific formats (e.g., "UC Berkeley")
    if (trimmedName.toUpperCase().startsWith(`${abbr} `)) {
      return `${fullName} at ${trimmedName.slice(abbr.length + 1)}`;
    }
  }

  // Return original name with proper capitalization
  return trimmedName.replace(/\w\S*/g, (txt) => 
    txt.charAt(0).toUpperCase() + txt.slice(1).toLowerCase()
  );
}

/**
 * Truncates text with proper handling of Unicode and RTL text
 * @param text - Text to truncate
 * @param maxLength - Maximum length of the resulting string
 * @param respectRTL - Whether to respect RTL text direction
 * @returns Truncated text with proper directional markers
 * @throws {FormatError} If parameters are invalid
 */
export function truncateText(text: string, maxLength: number, respectRTL = true): string {
  if (!text) return '';
  if (maxLength < 1) {
    throw new FormatError('Max length must be positive');
  }

  if (text.length <= maxLength) return text;

  // Detect text direction
  const rtl = respectRTL && /[\u0591-\u07FF\uFB1D-\uFDFD\uFE70-\uFEFC]/.test(text);
  
  // Find word boundary
  let truncated = text.slice(0, maxLength);
  const lastSpace = truncated.lastIndexOf(' ');
  
  if (lastSpace > 0) {
    truncated = truncated.slice(0, lastSpace);
  }

  // Add directional markers and ellipsis
  return rtl
    ? `\u202B${truncated}...\u202C`
    : `${truncated}...`;
}