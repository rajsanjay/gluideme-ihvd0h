// @ts-check
import { z } from 'zod'; // v3.21.0 - Runtime type validation
import type { PaginationParams, FilterParams, DateRange } from '../types/common';

/**
 * Valid search types for the application
 */
export type SearchType = 'requirements' | 'courses';

/**
 * Available fields for sorting search results
 */
export type SearchSortField = 'relevance' | 'name' | 'updatedAt' | 'institution';

/**
 * Search filter parameters for refining search results
 */
export interface SearchFilters {
  /** Types of institutions to include in search */
  institutionTypes: string[];
  /** Academic major categories to filter by */
  majorCategories: string[];
  /** Date range for requirement effectiveness */
  effectiveDate: DateRange;
  /** Status of requirements/courses */
  status: 'active' | 'pending' | 'archived';
}

/**
 * Comprehensive search request parameters
 */
export interface SearchParams {
  /** Search query string */
  query: string;
  /** Type of entities to search for */
  type: SearchType;
  /** Applied search filters */
  filters: SearchFilters;
  /** Field to sort results by */
  sortBy: SearchSortField;
  /** Pagination parameters */
  pagination: PaginationParams;
}

/**
 * Individual search result item structure
 */
export interface SearchResult {
  /** Unique identifier of the result */
  id: string;
  /** Type of the result (requirement/course) */
  type: SearchType;
  /** Title/name of the result */
  title: string;
  /** Description or summary */
  description: string;
  /** Associated institution name */
  institution: string;
  /** Academic major category */
  majorCategory: string;
  /** Effective date of the requirement/course */
  effectiveDate: string;
  /** Current status */
  status: 'active' | 'pending' | 'archived';
  /** Relevance score from search engine */
  score: number;
  /** Highlighted matches in search results */
  highlights: Record<string, string[]>;
}

/**
 * Complete search response structure
 */
export interface SearchResponse {
  /** Array of search results */
  results: SearchResult[];
  /** Total number of matching results */
  totalCount: number;
  /** Aggregated facet counts */
  facets: Record<string, Record<string, number>>;
  /** Search execution time in milliseconds */
  processingTime: number;
}

/**
 * Search suggestion/autocomplete result structure
 */
export interface SearchSuggestion {
  /** Suggested text */
  text: string;
  /** Type of suggestion */
  type: SearchType;
  /** Ranges for highlighting matches */
  highlightRanges: Array<{
    start: number;
    end: number;
  }>;
}

/**
 * Runtime validation schemas for search types
 */
export const searchSchemas = {
  searchFilters: z.object({
    institutionTypes: z.array(z.string()),
    majorCategories: z.array(z.string()),
    effectiveDate: z.object({
      startDate: z.string().datetime(),
      endDate: z.string().datetime()
    }),
    status: z.enum(['active', 'pending', 'archived'])
  }),

  searchParams: z.object({
    query: z.string(),
    type: z.enum(['requirements', 'courses']),
    filters: z.lazy(() => searchSchemas.searchFilters),
    sortBy: z.enum(['relevance', 'name', 'updatedAt', 'institution']),
    pagination: z.object({
      page: z.number().int().positive(),
      pageSize: z.number().int().positive()
    })
  }),

  searchResult: z.object({
    id: z.string(),
    type: z.enum(['requirements', 'courses']),
    title: z.string(),
    description: z.string(),
    institution: z.string(),
    majorCategory: z.string(),
    effectiveDate: z.string().datetime(),
    status: z.enum(['active', 'pending', 'archived']),
    score: z.number(),
    highlights: z.record(z.array(z.string()))
  }),

  searchResponse: z.object({
    results: z.array(z.lazy(() => searchSchemas.searchResult)),
    totalCount: z.number().int().nonnegative(),
    facets: z.record(z.record(z.number())),
    processingTime: z.number().positive()
  }),

  searchSuggestion: z.object({
    text: z.string(),
    type: z.enum(['requirements', 'courses']),
    highlightRanges: z.array(z.object({
      start: z.number().int().nonnegative(),
      end: z.number().int().positive()
    }))
  })
};