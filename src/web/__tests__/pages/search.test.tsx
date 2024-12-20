import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { axe, toHaveNoViolations } from 'jest-axe';
import SearchPage from '../../app/search/page';
import { useSearch } from '../../hooks/useSearch';

// Add jest-axe matcher
expect.extend(toHaveNoViolations);

// Mock useSearch hook
vi.mock('../../hooks/useSearch', () => ({
  useSearch: vi.fn()
}));

// Mock ResizeObserver
vi.mock('resize-observer-polyfill', () => ({
  default: vi.fn().mockImplementation(() => ({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn()
  }))
}));

// Test data
const mockSearchResults = [
  {
    id: '1',
    type: 'requirements',
    title: 'Computer Science Transfer Requirements',
    description: 'Transfer requirements for CS program',
    institution: 'UC Berkeley',
    majorCategory: 'STEM',
    effectiveDate: '2023-09-01',
    status: 'active',
    score: 0.95,
    highlights: {}
  }
];

const mockSearchState = {
  query: '',
  type: 'requirements',
  filters: {
    institutionTypes: [],
    majorCategories: [],
    effectiveDate: { startDate: '', endDate: '' },
    status: 'active'
  }
};

describe('SearchPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Setup default mock implementation
    (useSearch as jest.Mock).mockReturnValue({
      searchState: mockSearchState,
      searchResults: [],
      totalResults: 0,
      isLoading: false,
      error: null,
      handleQueryChange: vi.fn(),
      handleTypeChange: vi.fn(),
      handleFiltersChange: vi.fn(),
      handlePageChange: vi.fn(),
      paginationParams: { page: 1, pageSize: 20 }
    });
  });

  describe('Rendering', () => {
    it('should render search form and filters', () => {
      render(<SearchPage />);
      
      expect(screen.getByRole('search')).toBeInTheDocument();
      expect(screen.getByPlaceholder(/search requirements or courses/i)).toBeInTheDocument();
      expect(screen.getByRole('complementary')).toHaveTextContent(/filters/i);
    });

    it('should render results grid when results are available', async () => {
      (useSearch as jest.Mock).mockReturnValue({
        ...mockSearchState,
        searchResults: mockSearchResults,
        totalResults: 1
      });

      render(<SearchPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Computer Science Transfer Requirements')).toBeInTheDocument();
        expect(screen.getByText('UC Berkeley')).toBeInTheDocument();
      });
    });

    it('should render loading state correctly', () => {
      (useSearch as jest.Mock).mockReturnValue({
        ...mockSearchState,
        isLoading: true
      });

      render(<SearchPage />);
      expect(screen.getByRole('status')).toHaveTextContent(/searching/i);
    });

    it('should render error state correctly', () => {
      (useSearch as jest.Mock).mockReturnValue({
        ...mockSearchState,
        error: new Error('Search failed')
      });

      render(<SearchPage />);
      expect(screen.getByRole('alert')).toHaveTextContent(/search failed/i);
    });
  });

  describe('Search Functionality', () => {
    it('should handle search query changes', async () => {
      const handleQueryChange = vi.fn();
      (useSearch as jest.Mock).mockReturnValue({
        ...mockSearchState,
        handleQueryChange
      });

      render(<SearchPage />);
      
      const searchInput = screen.getByPlaceholder(/search requirements or courses/i);
      await userEvent.type(searchInput, 'computer science');

      expect(handleQueryChange).toHaveBeenCalledWith('computer science');
    });

    it('should handle search type changes', async () => {
      const handleTypeChange = vi.fn();
      (useSearch as jest.Mock).mockReturnValue({
        ...mockSearchState,
        handleTypeChange
      });

      render(<SearchPage />);
      
      const coursesRadio = screen.getByLabelText(/courses/i);
      await userEvent.click(coursesRadio);

      expect(handleTypeChange).toHaveBeenCalledWith('courses');
    });

    it('should handle filter changes', async () => {
      const handleFiltersChange = vi.fn();
      (useSearch as jest.Mock).mockReturnValue({
        ...mockSearchState,
        handleFiltersChange
      });

      render(<SearchPage />);
      
      const institutionFilter = screen.getByLabelText(/institution types/i);
      await userEvent.click(institutionFilter);
      await userEvent.click(screen.getByText('UC System'));

      expect(handleFiltersChange).toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    it('should have no accessibility violations', async () => {
      const { container } = render(<SearchPage />);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should handle keyboard navigation', async () => {
      render(<SearchPage />);
      
      const searchInput = screen.getByRole('searchbox');
      searchInput.focus();
      
      await userEvent.keyboard('{Tab}');
      expect(screen.getByLabelText(/requirements/i)).toHaveFocus();
      
      await userEvent.keyboard('{Tab}');
      expect(screen.getByLabelText(/courses/i)).toHaveFocus();
    });

    it('should announce search results to screen readers', async () => {
      (useSearch as jest.Mock).mockReturnValue({
        ...mockSearchState,
        searchResults: mockSearchResults,
        totalResults: 1
      });

      render(<SearchPage />);
      
      const announcement = screen.getByRole('status');
      expect(announcement).toHaveTextContent(/1 results? found/i);
    });
  });

  describe('Performance', () => {
    it('should meet search latency requirements', async () => {
      const startTime = performance.now();
      
      (useSearch as jest.Mock).mockReturnValue({
        ...mockSearchState,
        searchResults: mockSearchResults,
        totalResults: 1
      });

      render(<SearchPage />);
      
      const searchInput = screen.getByRole('searchbox');
      await userEvent.type(searchInput, 'computer science');

      const endTime = performance.now();
      const latency = endTime - startTime;

      expect(latency).toBeLessThan(200); // 200ms requirement from specs
    });

    it('should handle large result sets efficiently', async () => {
      const largeResultSet = Array.from({ length: 1000 }, (_, i) => ({
        ...mockSearchResults[0],
        id: `result-${i}`
      }));

      (useSearch as jest.Mock).mockReturnValue({
        ...mockSearchState,
        searchResults: largeResultSet,
        totalResults: largeResultSet.length
      });

      const { container } = render(<SearchPage />);
      
      // Check if virtualization is working
      const resultItems = container.querySelectorAll('[role="article"]');
      expect(resultItems.length).toBeLessThan(largeResultSet.length);
    });
  });

  describe('Error Handling', () => {
    it('should handle network errors gracefully', async () => {
      const networkError = new Error('Network error');
      (useSearch as jest.Mock).mockReturnValue({
        ...mockSearchState,
        error: networkError
      });

      render(<SearchPage />);
      
      expect(screen.getByRole('alert')).toHaveTextContent(/network error/i);
      expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
    });

    it('should handle validation errors appropriately', async () => {
      const validationError = new Error('Invalid search parameters');
      (useSearch as jest.Mock).mockReturnValue({
        ...mockSearchState,
        error: validationError
      });

      render(<SearchPage />);
      
      expect(screen.getByRole('alert')).toHaveTextContent(/invalid search parameters/i);
    });
  });
});