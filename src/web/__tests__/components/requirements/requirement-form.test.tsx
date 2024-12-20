import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import { vi } from 'vitest';
import { RequirementForm, type RequirementFormProps } from '../../../components/requirements/requirement-form';
import { createRequirement, updateRequirement } from '../../../lib/api/requirements';

// Add jest-axe matchers
expect.extend(toHaveNoViolations);

// Mock API functions
vi.mock('../../../lib/api/requirements', () => ({
  createRequirement: vi.fn(),
  updateRequirement: vi.fn()
}));

// Mock toast notifications
const mockToast = {
  show: vi.fn()
};
vi.mock('../../../hooks/useToast', () => ({
  useToast: () => mockToast
}));

// Test data
const mockInitialValues = {
  sourceInstitutionId: 'inst-1',
  targetInstitutionId: 'inst-2',
  majorCode: 'CS',
  title: 'Computer Science Transfer Requirements',
  description: 'Requirements for CS transfer',
  type: 'major' as const,
  rules: {
    courses: [
      {
        sourceCode: 'CS101',
        targetCode: 'COMP101',
        credits: 3
      }
    ],
    totalCredits: 60,
    minimumGPA: 3.0
  },
  status: 'draft' as const,
  effectiveDate: '2024-01-01'
};

describe('RequirementForm', () => {
  let user: ReturnType<typeof userEvent.setup>;

  beforeEach(() => {
    user = userEvent.setup();
    vi.clearAllMocks();
    (createRequirement as jest.Mock).mockResolvedValue({ data: { id: '123' } });
    (updateRequirement as jest.Mock).mockResolvedValue({ data: { id: '123' } });
  });

  const renderForm = (props: Partial<RequirementFormProps> = {}) => {
    const defaultProps: RequirementFormProps = {
      onSubmit: vi.fn(),
      ...props
    };
    return render(<RequirementForm {...defaultProps} />);
  };

  describe('Form Rendering', () => {
    it('renders all required form fields', () => {
      renderForm();

      expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/type/i)).toBeInTheDocument();
      expect(screen.getByText(/course requirements/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/minimum gpa/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/total credits/i)).toBeInTheDocument();
    });

    it('populates form with initial values', () => {
      renderForm({ initialValues: mockInitialValues });

      expect(screen.getByLabelText(/title/i)).toHaveValue(mockInitialValues.title);
      expect(screen.getByLabelText(/description/i)).toHaveValue(mockInitialValues.description);
      expect(screen.getByLabelText(/minimum gpa/i)).toHaveValue(String(mockInitialValues.rules.minimumGPA));
    });
  });

  describe('Form Validation', () => {
    it('validates required fields on submit', async () => {
      const onSubmit = vi.fn();
      renderForm({ onSubmit });

      await user.click(screen.getByRole('button', { name: /create requirement/i }));

      expect(await screen.findByText(/title is required/i)).toBeInTheDocument();
      expect(onSubmit).not.toHaveBeenCalled();
    });

    it('validates minimum GPA range', async () => {
      renderForm({ initialValues: mockInitialValues });

      const gpaInput = screen.getByLabelText(/minimum gpa/i);
      await user.clear(gpaInput);
      await user.type(gpaInput, '5.0');
      await user.tab();

      expect(await screen.findByText(/gpa must be between 0 and 4/i)).toBeInTheDocument();
    });

    it('validates course requirements', async () => {
      renderForm();

      await user.click(screen.getByText(/add course requirement/i));
      const courseSection = screen.getByRole('region', { name: /course requirements/i });
      
      await user.click(within(courseSection).getByRole('button', { name: /create requirement/i }));

      expect(await screen.findByText(/source course code is required/i)).toBeInTheDocument();
    });
  });

  describe('Form Submission', () => {
    it('calls onSubmit with valid form data', async () => {
      const onSubmit = vi.fn();
      renderForm({ onSubmit, initialValues: mockInitialValues });

      await user.click(screen.getByRole('button', { name: /create requirement/i }));

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({
          title: mockInitialValues.title,
          type: mockInitialValues.type
        }));
      });
    });

    it('handles submission errors gracefully', async () => {
      const error = new Error('API Error');
      (createRequirement as jest.Mock).mockRejectedValue(error);
      
      renderForm({ initialValues: mockInitialValues });

      await user.click(screen.getByRole('button', { name: /create requirement/i }));

      await waitFor(() => {
        expect(mockToast.show).toHaveBeenCalledWith(
          expect.objectContaining({
            type: 'error',
            message: expect.stringContaining('error')
          })
        );
      });
    });
  });

  describe('Accessibility', () => {
    it('meets WCAG 2.1 AA standards', async () => {
      const { container } = renderForm({ initialValues: mockInitialValues });
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('supports keyboard navigation', async () => {
      renderForm();
      
      await user.tab();
      expect(screen.getByLabelText(/title/i)).toHaveFocus();

      await user.tab();
      expect(screen.getByLabelText(/type/i)).toHaveFocus();
    });

    it('provides appropriate ARIA labels', () => {
      renderForm();

      const requiredFields = screen.getAllByRole('textbox', { name: /required/i });
      requiredFields.forEach(field => {
        expect(field).toHaveAttribute('aria-required', 'true');
      });
    });
  });

  describe('Responsive Behavior', () => {
    it('adjusts layout for mobile viewport', () => {
      global.innerWidth = 375;
      global.dispatchEvent(new Event('resize'));
      
      renderForm();

      const form = screen.getByRole('form');
      expect(form).toHaveClass('space-y-6');
      // Add more specific responsive layout checks
    });

    it('maintains usability on touch devices', async () => {
      renderForm();

      const addButton = screen.getByRole('button', { name: /add course requirement/i });
      await user.touch(addButton);

      expect(screen.getByRole('region', { name: /course requirements/i }))
        .toBeInTheDocument();
    });
  });

  describe('Auto-save Functionality', () => {
    it('auto-saves form when enabled', async () => {
      const onSubmit = vi.fn();
      renderForm({ onSubmit, autoSave: true, initialValues: mockInitialValues });

      const titleInput = screen.getByLabelText(/title/i);
      await user.type(titleInput, ' Updated');

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalled();
      }, { timeout: 2500 });
    });
  });
});