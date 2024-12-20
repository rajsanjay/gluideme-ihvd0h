/**
 * @fileoverview API client functions for search operations including full-text search,
 * autocomplete suggestions, and similarity search using MeiliSearch and Pinecone integration.
 * Implements caching, error handling, and performance optimizations.
 * @version 1.0.0
 */

import type { AxiosResponse } from 'axios'; // ^1.4.0
import retry from 'axios-retry'; // ^3.5.0
import {
  SearchParams,
  SearchResponse,
  SearchSuggestion,
  searchSchemas
} from '../../types/search';
import apiClient from '../../config/api';

// Performance budget for search operations in milliseconds
const PERFORMANCE_BUDGET = {
  search: 200,
  suggestions: 100,
  similarity: 150
};

// Cache configuration for different search operations
const CACHE_CONFIG = {
  search: {
    maxAge: 5 * 60 * 1000, // 5 minutes
    excludeFromCache: (params: SearchParams) => 
      params.filters.status === 'pending' // Don't cache pending items
  },
  suggestions: {
    maxAge: 15 * 60 * 1000, // 15 minutes
    staleWhileRevalidate: true
  },
  similarity: {
    maxAge: 30 * 60 * 1000, // 30 minutes
    revalidateOnFocus: true
  }
};

/**
 * Performs a search across transfer requirements using MeiliSearch with caching
 * and retry mechanisms.
 * 
 * @param params - Search parameters including query, filters, and pagination
 * @returns Promise resolving to search results with performance metrics
 * @throws {ApiError} When search operation fails
 */
export async function searchRequirements(
  params: SearchParams
): Promise<SearchResponse> {
  // Validate search parameters
  const validatedParams = searchSchemas.searchParams.parse(params);
  
  const startTime = performance.now();

  try {
    // Configure retry strategy for search requests
    retry(apiClient, {
      retries: 2,
      retryDelay: (retryCount) => retryCount * 300,
      retryCondition: (error) => {
        return retry.isNetworkOrIdempotentRequestError(error) ||
               error.response?.status === 503;
      }
    });

    const response: AxiosResponse<SearchResponse> = await apiClient.post(
      '/api/v1/search',
      validatedParams,
      {
        headers: {
          'X-Search-Client': 'meilisearch',
          'X-Cache-Control': CACHE_CONFIG.search.maxAge.toString()
        },
        timeout: PERFORMANCE_BUDGET.search
      }
    );

    const validatedResponse = searchSchemas.searchResponse.parse(response.data);
    
    // Log performance metrics if exceeding budget
    const duration = performance.now() - startTime;
    if (duration > PERFORMANCE_BUDGET.search) {
      console.warn(`Search operation exceeded performance budget: ${duration}ms`);
    }

    return validatedResponse;
  } catch (error) {
    console.error('Search operation failed:', error);
    throw error;
  }
}

/**
 * Retrieves autocomplete suggestions for search queries with deduplication.
 * 
 * @param query - Search query string to get suggestions for
 * @param type - Type of suggestions to retrieve
 * @returns Promise resolving to deduplicated search suggestions
 * @throws {ApiError} When suggestion retrieval fails
 */
export async function getSearchSuggestions(
  query: string,
  type: SearchParams['type']
): Promise<SearchSuggestion[]> {
  if (!query.trim()) {
    return [];
  }

  const startTime = performance.now();

  try {
    const response: AxiosResponse<SearchSuggestion[]> = await apiClient.get(
      '/api/v1/search/autocomplete',
      {
        params: { query, type },
        headers: {
          'X-Cache-Control': CACHE_CONFIG.suggestions.maxAge.toString()
        },
        timeout: PERFORMANCE_BUDGET.suggestions
      }
    );

    // Deduplicate suggestions
    const suggestions = Array.from(
      new Map(
        response.data.map(suggestion => [suggestion.text, suggestion])
      ).values()
    );

    // Validate suggestions
    const validatedSuggestions = suggestions.map(suggestion =>
      searchSchemas.searchSuggestion.parse(suggestion)
    );

    const duration = performance.now() - startTime;
    if (duration > PERFORMANCE_BUDGET.suggestions) {
      console.warn(`Suggestions operation exceeded performance budget: ${duration}ms`);
    }

    return validatedSuggestions;
  } catch (error) {
    console.error('Suggestion retrieval failed:', error);
    throw error;
  }
}

/**
 * Performs similarity search using Pinecone vector database with performance optimization.
 * 
 * @param requirementId - ID of the requirement to find similar items for
 * @param limit - Maximum number of similar items to return
 * @returns Promise resolving to similar requirements with similarity scores
 * @throws {ApiError} When similarity search fails
 */
export async function findSimilarRequirements(
  requirementId: string,
  limit: number = 5
): Promise<SearchResponse> {
  if (!requirementId) {
    throw new Error('Requirement ID is required');
  }

  const startTime = performance.now();

  try {
    const response: AxiosResponse<SearchResponse> = await apiClient.post(
      '/api/v1/search/similar',
      {
        requirementId,
        limit: Math.min(Math.max(limit, 1), 20) // Clamp between 1 and 20
      },
      {
        headers: {
          'X-Search-Client': 'pinecone',
          'X-Cache-Control': CACHE_CONFIG.similarity.maxAge.toString()
        },
        timeout: PERFORMANCE_BUDGET.similarity
      }
    );

    const validatedResponse = searchSchemas.searchResponse.parse(response.data);

    // Filter results by minimum similarity score
    validatedResponse.results = validatedResponse.results.filter(
      result => result.score >= 0.7 // Minimum similarity threshold
    );

    const duration = performance.now() - startTime;
    if (duration > PERFORMANCE_BUDGET.similarity) {
      console.warn(`Similarity search exceeded performance budget: ${duration}ms`);
    }

    return validatedResponse;
  } catch (error) {
    console.error('Similarity search failed:', error);
    throw error;
  }
}