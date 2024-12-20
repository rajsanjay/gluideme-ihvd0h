import * as React from 'react';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { expect, describe, it, beforeEach } from '@testing-library/jest-dom/matchers';
import Button, { buttonVariants } from '../../components/common/button';

// Version: ^14.0.0 - @testing-library/react
// Version: ^5.16.5 - @testing-library/jest-dom

/**
 * Mock matchMedia for testing reduced motion preferences
 */
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

/**
 * Helper function to render Button component with props
 */
const renderButton = (props: Partial<React.ComponentProps<typeof Button>> = {}) => {
  const defaultProps = {
    children: 'Test Button',
    onClick: jest.fn(),
  };
  return render(<Button {...defaultProps} {...props} />);
};

describe('Button Component', () => {
  let mockOnClick: jest.Mock;

  beforeEach(() => {
    mockOnClick = jest.fn();
  });

  describe('Basic Rendering', () => {
    it('renders with default props', () => {
      renderButton();
      const button = screen.getByRole('button', { name: /test button/i });
      
      expect(button).toBeInTheDocument();
      expect(button).toHaveClass(buttonVariants({ variant: 'primary', size: 'md' }));
      expect(button).not.toBeDisabled();
      expect(button).toHaveAttribute('type', 'button');
    });

    it('renders with custom className', () => {
      const customClass = 'custom-class';
      renderButton({ className: customClass });
      
      const button = screen.getByRole('button');
      expect(button).toHaveClass(customClass);
    });
  });

  describe('Variants', () => {
    it.each(['primary', 'secondary', 'outline', 'ghost'] as const)(
      'renders %s variant with correct styles',
      (variant) => {
        renderButton({ variant });
        const button = screen.getByRole('button');
        expect(button).toHaveClass(buttonVariants({ variant }));
      }
    );
  });

  describe('Sizes', () => {
    it.each(['sm', 'md', 'lg'] as const)(
      'renders %s size with correct dimensions',
      (size) => {
        renderButton({ size });
        const button = screen.getByRole('button');
        expect(button).toHaveClass(buttonVariants({ size }));
      }
    );
  });

  describe('Loading State', () => {
    it('displays loading spinner and prevents interaction', () => {
      renderButton({ isLoading: true, onClick: mockOnClick });
      const button = screen.getByRole('button');
      const spinner = within(button).getByRole('status');

      expect(spinner).toBeInTheDocument();
      expect(button).toHaveAttribute('aria-busy', 'true');
      expect(button).toBeDisabled();

      fireEvent.click(button);
      expect(mockOnClick).not.toHaveBeenCalled();
    });

    it('preserves button text during loading', () => {
      const buttonText = 'Save Changes';
      renderButton({ isLoading: true, children: buttonText });
      
      expect(screen.getByText(buttonText)).toBeInTheDocument();
      expect(screen.getByRole('status')).toBeInTheDocument();
    });
  });

  describe('Disabled State', () => {
    it('prevents interaction when disabled', () => {
      renderButton({ isDisabled: true, onClick: mockOnClick });
      const button = screen.getByRole('button');

      expect(button).toBeDisabled();
      expect(button).toHaveAttribute('aria-disabled', 'true');

      fireEvent.click(button);
      expect(mockOnClick).not.toHaveBeenCalled();
    });
  });

  describe('Icon Integration', () => {
    const MockIcon = () => <span data-testid="mock-icon">icon</span>;

    it('renders left icon correctly', () => {
      renderButton({ leftIcon: <MockIcon /> });
      const icon = screen.getByTestId('mock-icon');
      const button = screen.getByRole('button');
      
      expect(icon).toBeInTheDocument();
      expect(button.firstElementChild).toContainElement(icon);
    });

    it('renders right icon correctly', () => {
      renderButton({ rightIcon: <MockIcon /> });
      const icon = screen.getByTestId('mock-icon');
      const button = screen.getByRole('button');
      
      expect(icon).toBeInTheDocument();
      expect(button.lastElementChild).toContainElement(icon);
    });

    it('handles both icons simultaneously', () => {
      renderButton({
        leftIcon: <MockIcon data-testid="left-icon" />,
        rightIcon: <MockIcon data-testid="right-icon" />
      });
      
      expect(screen.getByTestId('left-icon')).toBeInTheDocument();
      expect(screen.getByTestId('right-icon')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('supports custom aria-label', () => {
      const ariaLabel = 'Custom Button Label';
      renderButton({ ariaLabel });
      
      expect(screen.getByRole('button')).toHaveAttribute('aria-label', ariaLabel);
    });

    it('supports custom aria-describedby', () => {
      const describedBy = 'button-description';
      renderButton({ ariaDescribedBy: describedBy });
      
      expect(screen.getByRole('button')).toHaveAttribute('aria-describedby', describedBy);
    });

    it('maintains focus visibility', () => {
      renderButton();
      const button = screen.getByRole('button');
      
      button.focus();
      expect(button).toHaveFocus();
      expect(button).toHaveClass('focus-visible:ring-2');
    });

    it('handles keyboard interaction', () => {
      renderButton({ onClick: mockOnClick });
      const button = screen.getByRole('button');

      // Test Space key
      fireEvent.keyDown(button, { key: ' ' });
      fireEvent.keyUp(button, { key: ' ' });
      expect(mockOnClick).toHaveBeenCalledTimes(1);

      // Test Enter key
      fireEvent.keyDown(button, { key: 'Enter' });
      fireEvent.keyUp(button, { key: 'Enter' });
      expect(mockOnClick).toHaveBeenCalledTimes(2);
    });
  });

  describe('Event Handling', () => {
    it('calls onClick handler when clicked', () => {
      renderButton({ onClick: mockOnClick });
      const button = screen.getByRole('button');

      fireEvent.click(button);
      expect(mockOnClick).toHaveBeenCalledTimes(1);
    });

    it('prevents default form submission', () => {
      const { container } = render(
        <form onSubmit={mockOnClick}>
          <Button type="button">Test Button</Button>
        </form>
      );

      const form = container.querySelector('form')!;
      const button = screen.getByRole('button');

      fireEvent.submit(form);
      fireEvent.click(button);
      
      expect(mockOnClick).toHaveBeenCalledTimes(1);
      expect(button).toHaveAttribute('type', 'button');
    });
  });
});