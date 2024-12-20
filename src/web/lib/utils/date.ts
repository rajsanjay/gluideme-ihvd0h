/**
 * @fileoverview Enterprise-grade date manipulation utilities with comprehensive validation
 * @version 1.0.0
 */

import { 
  format, 
  parse, 
  isValid, 
  isAfter, 
  isBefore, 
  addDays, 
  subDays,
  startOfDay,
  endOfDay,
  startOfWeek,
  endOfWeek,
  startOfMonth,
  endOfMonth,
  startOfYear,
  endOfYear
} from 'date-fns'; // v2.30.0

import type { DateRange } from '../../types/common';

// Standard date format constants
export const DATE_FORMAT = 'yyyy-MM-dd' as const;
export const DATETIME_FORMAT = 'yyyy-MM-dd HH:mm:ss' as const;
export const DISPLAY_DATE_FORMAT = 'MMM d, yyyy' as const;
export const DISPLAY_DATETIME_FORMAT = 'MMM d, yyyy h:mm a' as const;

// Date validation boundaries
export const MIN_VALID_DATE = '1900-01-01' as const;
export const MAX_VALID_DATE = '2100-12-31' as const;

// Academic term constants
export const ACADEMIC_TERMS = {
  FALL: 'Fall',
  SPRING: 'Spring',
  SUMMER: 'Summer',
  WINTER: 'Winter'
} as const;

/**
 * Custom error class for date-related errors
 */
class DateUtilError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'DateUtilError';
  }
}

/**
 * Formats a date string or Date object into standardized format with enhanced error handling
 * @param date - Date to format
 * @param formatStr - Target format string
 * @returns Formatted date string
 * @throws {DateUtilError} If date is invalid or outside acceptable range
 */
export function formatDate(date: Date | string, formatStr: string = DATE_FORMAT): string {
  try {
    const parsedDate = date instanceof Date ? date : parseDate(date);
    
    if (!isValidDate(parsedDate.toISOString())) {
      throw new DateUtilError('Date is outside acceptable range');
    }

    const formatted = format(parsedDate, formatStr);
    
    // Validate output format
    if (!formatted || formatted === 'Invalid Date') {
      throw new DateUtilError('Failed to format date');
    }

    return formatted;
  } catch (error) {
    throw new DateUtilError(`Failed to format date: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Parses a date string into a Date object with comprehensive validation
 * @param dateStr - Date string to parse
 * @returns Parsed Date object
 * @throws {DateUtilError} If date string is invalid or unparseable
 */
export function parseDate(dateStr: string): Date {
  try {
    // Try parsing with different known formats
    const formats = [DATE_FORMAT, DATETIME_FORMAT, 'ISO'];
    let parsedDate: Date | null = null;

    for (const format of formats) {
      if (format === 'ISO') {
        parsedDate = new Date(dateStr);
      } else {
        parsedDate = parse(dateStr, format, new Date());
      }

      if (isValid(parsedDate)) {
        break;
      }
    }

    if (!parsedDate || !isValid(parsedDate)) {
      throw new DateUtilError('Invalid date string format');
    }

    return parsedDate;
  } catch (error) {
    throw new DateUtilError(`Failed to parse date: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Validates if a date string is valid and within acceptable range
 * @param dateStr - Date string to validate
 * @returns Boolean indicating if date is valid
 */
export function isValidDate(dateStr: string): boolean {
  try {
    const date = parseDate(dateStr);
    const minDate = parseDate(MIN_VALID_DATE);
    const maxDate = parseDate(MAX_VALID_DATE);

    return (
      isValid(date) &&
      isAfter(date, minDate) &&
      isBefore(date, maxDate)
    );
  } catch {
    return false;
  }
}

/**
 * Gets start and end dates for a given range type with validation
 * @param rangeType - Type of range to calculate ('day', 'week', 'month', 'year')
 * @returns DateRange object with validated start and end dates
 * @throws {DateUtilError} If range type is invalid
 */
export function getDateRange(rangeType: 'day' | 'week' | 'month' | 'year'): DateRange {
  try {
    const now = new Date();
    let startDate: Date;
    let endDate: Date;

    switch (rangeType) {
      case 'day':
        startDate = startOfDay(now);
        endDate = endOfDay(now);
        break;
      case 'week':
        startDate = startOfWeek(now, { weekStartsOn: 1 });
        endDate = endOfWeek(now, { weekStartsOn: 1 });
        break;
      case 'month':
        startDate = startOfMonth(now);
        endDate = endOfMonth(now);
        break;
      case 'year':
        startDate = startOfYear(now);
        endDate = endOfYear(now);
        break;
      default:
        throw new DateUtilError('Invalid range type');
    }

    return {
      startDate: formatDate(startDate),
      endDate: formatDate(endDate)
    };
  } catch (error) {
    throw new DateUtilError(`Failed to calculate date range: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Formats a date into academic year format with enhanced validation
 * @param date - Date to format
 * @returns Academic year string (e.g., '2023-2024')
 * @throws {DateUtilError} If date is invalid
 */
export function formatAcademicYear(date: Date | string): string {
  try {
    const parsedDate = date instanceof Date ? date : parseDate(date);
    
    if (!isValidDate(parsedDate.toISOString())) {
      throw new DateUtilError('Invalid date for academic year calculation');
    }

    // Academic year starts in Fall (August)
    const year = parsedDate.getFullYear();
    const month = parsedDate.getMonth();
    
    // If month is August or later, academic year starts in current year
    // Otherwise, academic year started in previous year
    const academicStartYear = month >= 7 ? year : year - 1;
    
    return `${academicStartYear}-${academicStartYear + 1}`;
  } catch (error) {
    throw new DateUtilError(`Failed to format academic year: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Formats a date into academic term format with comprehensive term detection
 * @param date - Date to format
 * @returns Academic term string (e.g., 'Fall 2023')
 * @throws {DateUtilError} If date is invalid
 */
export function formatAcademicTerm(date: Date | string): string {
  try {
    const parsedDate = date instanceof Date ? date : parseDate(date);
    
    if (!isValidDate(parsedDate.toISOString())) {
      throw new DateUtilError('Invalid date for academic term calculation');
    }

    const month = parsedDate.getMonth();
    const year = parsedDate.getFullYear();

    // Determine term based on month
    let term: string;
    if (month >= 7 && month <= 11) {
      term = ACADEMIC_TERMS.FALL;
    } else if (month >= 0 && month <= 4) {
      term = ACADEMIC_TERMS.SPRING;
    } else {
      term = ACADEMIC_TERMS.SUMMER;
    }

    // Adjust year for Spring/Summer terms
    const termYear = term === ACADEMIC_TERMS.FALL ? year : year;
    
    return `${term} ${termYear}`;
  } catch (error) {
    throw new DateUtilError(`Failed to format academic term: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}