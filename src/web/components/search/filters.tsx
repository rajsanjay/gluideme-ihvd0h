/**
 * @file Search Filters Component
 * @version 1.0.0
 * @description Accessible and performant filter controls for search interface with WCAG 2.1 AA compliance
 */

import React, { useCallback, useEffect, useState } from 'react';
import { useDebounce } from 'use-debounce'; // ^9.0.0
import { cn } from '@shadcn/ui'; // ^0.1.0
import Select from '../common/select';
import type { SearchFilters } from '../../types/search';
import { theme } from '../../config/theme';

// Constants for filter options
const INSTITUTION_TYPES = [
  { value: 'uc', label: 'UC System', disabled: false },
  { value: 'csu', label: 'CSU System', disabled: false },
  { value: 'ccc', label: 'Community Colleges', disabled: false },
  { value: 'private', label: 'Private Institutions', disabled: false }
];

const MAJOR_CATEGORIES = [
  { value: 'stem', label: 'STEM', disabled: false },
  { value: 'humanities', label: 'Humanities', disabled: false },
  { value: 'business', label: 'Business', disabled: false },
  { value: 'arts', label: 'Arts', disabled: false },
  { value: 'social_sciences', label: 'Social Sciences', disabled: false }
];

const STATUS_OPTIONS = [
  { value: 'active', label: 'Active', disabled: false },
  { value: 'pending', label: 'Pending Review', disabled: false },
  { value: 'archived', label: 'Archived', disabled: false }
];

// Debounce delay for filter updates
const DEBOUNCE_MS = 300;

interface SearchFiltersProps {
  /** Current filter state */
  filters: SearchFilters;
  /** Callback for filter changes */
  onChange: (filters: SearchFilters) => void;
  /** Optional CSS classes */
  className?: string;
}

interface FilterError {
  field: string;
  message: string;
}

export const SearchFilters: React.FC<SearchFiltersProps> = ({
  filters,
  onChange,
  className
}) => {
  // Local state for filter values
  const [localFilters, setLocalFilters] = useState<SearchFilters>(filters);
  const [error, setError] = useState<FilterError | null>(null);
  
  // Debounced filter updates to prevent rapid re-renders
  const [debouncedFilters] = useDebounce(localFilters, DEBOUNCE_MS);

  // Validate and update filters
  const validateAndUpdateFilters = useCallback((newFilters: Partial<SearchFilters>) => {
    try {
      const updatedFilters = {
        ...localFilters,
        ...newFilters
      };

      // Basic validation
      if (updatedFilters.institutionTypes.length > 0 && 
          updatedFilters.majorCategories.length > 0) {
        setError(null);
        setLocalFilters(updatedFilters);
      } else {
        setError({
          field: 'filters',
          message: 'Please select at least one institution type and major category'
        });
      }
    } catch (err) {
      setError({
        field: 'filters',
        message: 'Invalid filter selection'
      });
    }
  }, [localFilters]);

  // Handle institution type changes
  const handleInstitutionTypeChange = useCallback((selectedTypes: string[]) => {
    validateAndUpdateFilters({ institutionTypes: selectedTypes });
    
    // Announce changes to screen readers
    const message = `Selected institution types: ${selectedTypes.join(', ')}`;
    announceChange(message);
  }, [validateAndUpdateFilters]);

  // Handle major category changes
  const handleMajorCategoryChange = useCallback((selectedCategories: string[]) => {
    validateAndUpdateFilters({ majorCategories: selectedCategories });
    
    // Announce changes to screen readers
    const message = `Selected major categories: ${selectedCategories.join(', ')}`;
    announceChange(message);
  }, [validateAndUpdateFilters]);

  // Handle status changes
  const handleStatusChange = useCallback((status: string) => {
    validateAndUpdateFilters({ status: status as SearchFilters['status'] });
    
    // Announce changes to screen readers
    const message = `Filter status changed to: ${status}`;
    announceChange(message);
  }, [validateAndUpdateFilters]);

  // Utility function for screen reader announcements
  const announceChange = (message: string) => {
    const announcement = document.createElement('div');
    announcement.setAttribute('role', 'status');
    announcement.setAttribute('aria-live', 'polite');
    announcement.className = 'sr-only';
    announcement.textContent = message;
    document.body.appendChild(announcement);
    setTimeout(() => document.body.removeChild(announcement), 1000);
  };

  // Update parent component when debounced filters change
  useEffect(() => {
    if (!error) {
      onChange(debouncedFilters);
    }
  }, [debouncedFilters, error, onChange]);

  return (
    <div 
      className={cn(
        'flex flex-col gap-4 p-4 rounded-lg border',
        error && 'border-red-500',
        theme.getThemeValue('background'),
        className
      )}
      role="search"
      aria-label="Search filters"
    >
      <div className="space-y-2">
        <label 
          id="institution-type-label" 
          className="text-sm font-medium text-gray-700 dark:text-gray-300"
        >
          Institution Types
        </label>
        <Select
          value={localFilters.institutionTypes}
          onChange={handleInstitutionTypeChange}
          options={INSTITUTION_TYPES}
          placeholder="Select institution types"
          multiple
          error={error?.field === 'institutionTypes' ? error.message : undefined}
          aria-labelledby="institution-type-label"
          aria-invalid={error?.field === 'institutionTypes'}
        />
      </div>

      <div className="space-y-2">
        <label 
          id="major-category-label" 
          className="text-sm font-medium text-gray-700 dark:text-gray-300"
        >
          Major Categories
        </label>
        <Select
          value={localFilters.majorCategories}
          onChange={handleMajorCategoryChange}
          options={MAJOR_CATEGORIES}
          placeholder="Select major categories"
          multiple
          error={error?.field === 'majorCategories' ? error.message : undefined}
          aria-labelledby="major-category-label"
          aria-invalid={error?.field === 'majorCategories'}
        />
      </div>

      <div className="space-y-2">
        <label 
          id="status-label" 
          className="text-sm font-medium text-gray-700 dark:text-gray-300"
        >
          Status
        </label>
        <Select
          value={localFilters.status}
          onChange={handleStatusChange}
          options={STATUS_OPTIONS}
          placeholder="Select status"
          error={error?.field === 'status' ? error.message : undefined}
          aria-labelledby="status-label"
          aria-invalid={error?.field === 'status'}
        />
      </div>

      {error && (
        <div 
          className="text-red-500 text-sm mt-2" 
          role="alert"
          aria-live="polite"
        >
          {error.message}
        </div>
      )}
    </div>
  );
};

export default SearchFilters;