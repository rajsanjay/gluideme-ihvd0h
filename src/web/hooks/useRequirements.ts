/**
 * @fileoverview Custom React hook for managing transfer requirements with comprehensive features
 * including CRUD operations, real-time validation, caching, and accessibility support
 * @version 1.0.0
 */

import { useCallback, useRef, useState } from 'react'; // v18.2.0
import { useQuery, useMutation, useQueryClient } from 'react-query'; // v4.0.0
import debounce from 'lodash/debounce'; // v4.17.21
import type { 
  TransferRequirement,
  RequirementValidationResult,
  RequirementStatus,
  RequirementType
} from '../../types/requirements';
import { 
  getRequirements,
  getRequirementById,
  createRequirement,
  updateRequirement,
  deleteRequirement,
  validateCourses,
  getRequirementMetadata
} from '../../lib/api/requirements';
import { useToast } from '../useToast';
import type { PaginationParams, SortParams, FilterParams } from '../../types/common';

/**
 * Interface for requirement filter options
 */
interface RequirementFilters extends FilterParams {
  institutionId?: string;
  majorCode?: string;
  type?: RequirementType;
  status?: RequirementStatus;
  search?: string;
}

/**
 * Interface for requirement query options
 */
interface RequirementQueryOptions {
  pagination?: PaginationParams;
  sort?: SortParams;
  filters?: RequirementFilters;
}

/**
 * Interface for requirement operations
 */
interface RequirementOperations {
  create: (requirement: Partial<TransferRequirement>) => Promise<TransferRequirement>;
  update: (id: string, updates: Partial<TransferRequirement>) => Promise<TransferRequirement>;
  delete: (id: string) => Promise<void>;
  validate: (id: string, courses: string[]) => Promise<RequirementValidationResult>;
  refresh: () => void;
}

/**
 * Custom hook for managing transfer requirements
 */
export function useRequirements(options: RequirementQueryOptions = {}) {
  // Initialize React Query client
  const queryClient = useQueryClient();

  // Get toast notifications
  const toast = useToast();

  // Track current query options
  const [queryOptions, setQueryOptions] = useState<RequirementQueryOptions>(options);

  // Debounced search handler
  const debouncedSearch = useRef(
    debounce((search: string) => {
      setQueryOptions(prev => ({
        ...prev,
        filters: { ...prev.filters, search }
      }));
    }, 300)
  ).current;

  // Fetch requirements query
  const {
    data: requirementsData,
    isLoading,
    error,
    refetch
  } = useQuery(
    ['requirements', queryOptions],
    () => getRequirements({
      page: queryOptions.pagination?.page,
      limit: queryOptions.pagination?.pageSize,
      sort: queryOptions.sort?.sortBy,
      filters: queryOptions.filters
    }),
    {
      keepPreviousData: true,
      staleTime: 30000, // 30 seconds
      cacheTime: 300000, // 5 minutes
      onError: (error: Error) => {
        toast.show({
          message: 'Failed to fetch requirements',
          type: 'error',
          duration: 5000
        });
      }
    }
  );

  // Create requirement mutation
  const createMutation = useMutation(createRequirement, {
    onSuccess: (newRequirement) => {
      queryClient.invalidateQueries(['requirements']);
      toast.show({
        message: 'Requirement created successfully',
        type: 'success'
      });
    },
    onError: (error: Error) => {
      toast.show({
        message: 'Failed to create requirement',
        type: 'error'
      });
    }
  });

  // Update requirement mutation
  const updateMutation = useMutation(
    ({ id, updates }: { id: string; updates: Partial<TransferRequirement> }) =>
      updateRequirement(id, updates),
    {
      onSuccess: (updatedRequirement) => {
        queryClient.invalidateQueries(['requirements']);
        toast.show({
          message: 'Requirement updated successfully',
          type: 'success'
        });
      },
      onError: (error: Error) => {
        toast.show({
          message: 'Failed to update requirement',
          type: 'error'
        });
      }
    }
  );

  // Delete requirement mutation
  const deleteMutation = useMutation(deleteRequirement, {
    onSuccess: () => {
      queryClient.invalidateQueries(['requirements']);
      toast.show({
        message: 'Requirement deleted successfully',
        type: 'success'
      });
    },
    onError: (error: Error) => {
      toast.show({
        message: 'Failed to delete requirement',
        type: 'error'
      });
    }
  });

  // Validate courses mutation
  const validateMutation = useMutation(
    ({ id, courses }: { id: string; courses: string[] }) =>
      validateCourses(id, courses),
    {
      onError: (error: Error) => {
        toast.show({
          message: 'Course validation failed',
          type: 'error'
        });
      }
    }
  );

  // Requirement operations
  const operations: RequirementOperations = {
    create: async (requirement) => {
      return createMutation.mutateAsync(requirement);
    },
    update: async (id, updates) => {
      return updateMutation.mutateAsync({ id, updates });
    },
    delete: async (id) => {
      return deleteMutation.mutateAsync(id);
    },
    validate: async (id, courses) => {
      return validateMutation.mutateAsync({ id, courses });
    },
    refresh: () => {
      refetch();
    }
  };

  // Update pagination
  const updatePagination = useCallback((pagination: PaginationParams) => {
    setQueryOptions(prev => ({
      ...prev,
      pagination
    }));
  }, []);

  // Update sorting
  const updateSort = useCallback((sort: SortParams) => {
    setQueryOptions(prev => ({
      ...prev,
      sort
    }));
  }, []);

  // Update filters
  const updateFilters = useCallback((filters: RequirementFilters) => {
    setQueryOptions(prev => ({
      ...prev,
      filters: {
        ...prev.filters,
        ...filters
      }
    }));
  }, []);

  // Handle search
  const handleSearch = useCallback((search: string) => {
    debouncedSearch(search);
  }, [debouncedSearch]);

  return {
    // Data
    requirements: requirementsData?.data || [],
    total: requirementsData?.total || 0,
    totalPages: requirementsData?.totalPages || 0,

    // Loading state
    isLoading,
    error,

    // Query state
    pagination: queryOptions.pagination,
    sort: queryOptions.sort,
    filters: queryOptions.filters,

    // Operations
    operations,

    // State updates
    updatePagination,
    updateSort,
    updateFilters,
    handleSearch,

    // Mutation states
    isCreating: createMutation.isLoading,
    isUpdating: updateMutation.isLoading,
    isDeleting: deleteMutation.isLoading,
    isValidating: validateMutation.isLoading
  };
}