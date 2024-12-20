/**
 * @file Select Component
 * @version 1.0.0
 * @description A fully accessible and performant select component implementing WCAG 2.1 AA standards
 * with support for single/multi-select, virtualization, and theming.
 */

import React, { useCallback, useEffect, useRef, useState } from 'react'; // ^18.2.0
import { cn } from '@shadcn/ui'; // ^0.1.0
import { useVirtualizer } from '@tanstack/react-virtual'; // ^3.0.0
import type { SelectOption } from '../../types/common';
import { theme } from '../../config/theme';

// Constants for keyboard navigation and accessibility
const KEYS = {
  ENTER: 'Enter',
  SPACE: ' ',
  ESCAPE: 'Escape',
  ARROW_UP: 'ArrowUp',
  ARROW_DOWN: 'ArrowDown',
  HOME: 'Home',
  END: 'End',
  TAB: 'Tab',
} as const;

const TYPEAHEAD_TIMEOUT = 500;
const OPTION_HEIGHT = 40;

interface SelectProps {
  /** Current value(s) of the select */
  value: string | number | Array<string | number>;
  /** Callback fired when selection changes */
  onChange: (value: string | number | Array<string | number>) => void;
  /** Array of available options */
  options: SelectOption[];
  /** Placeholder text when no selection */
  placeholder?: string;
  /** Whether the select is disabled */
  disabled?: boolean;
  /** Error message for validation feedback */
  error?: string;
  /** Enable multi-select mode */
  multiple?: boolean;
  /** Additional CSS classes */
  className?: string;
  /** Enable virtualization for large datasets */
  virtualize?: boolean;
  /** Loading state indicator */
  loading?: boolean;
  /** Maximum height of dropdown */
  maxHeight?: number;
  /** Enable search functionality */
  searchable?: boolean;
}

export const Select: React.FC<SelectProps> = ({
  value,
  onChange,
  options,
  placeholder = 'Select an option',
  disabled = false,
  error,
  multiple = false,
  className,
  virtualize = false,
  loading = false,
  maxHeight = 300,
  searchable = false,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const [searchQuery, setSearchQuery] = useState('');
  const [typeaheadBuffer, setTypeaheadBuffer] = useState('');

  const containerRef = useRef<HTMLDivElement>(null);
  const listboxRef = useRef<HTMLUListElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const typeaheadTimeoutRef = useRef<NodeJS.Timeout>();

  // Setup virtualization if enabled
  const virtualizer = useVirtualizer({
    count: options.length,
    getScrollElement: () => listboxRef.current,
    estimateSize: () => OPTION_HEIGHT,
    overscan: 5,
    enabled: virtualize,
  });

  // Filter options based on search query
  const filteredOptions = searchable && searchQuery
    ? options.filter(option => 
        option.label.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : options;

  // Get display value for selected option(s)
  const getDisplayValue = useCallback(() => {
    if (multiple && Array.isArray(value)) {
      return value
        .map(v => options.find(o => o.value === v)?.label)
        .filter(Boolean)
        .join(', ');
    }
    return options.find(o => o.value === value)?.label || placeholder;
  }, [value, options, multiple, placeholder]);

  // Handle keyboard navigation
  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (disabled) return;

    switch (event.key) {
      case KEYS.ENTER:
      case KEYS.SPACE:
        event.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
        } else if (focusedIndex >= 0) {
          const option = filteredOptions[focusedIndex];
          handleOptionSelect(option);
        }
        break;

      case KEYS.ESCAPE:
        event.preventDefault();
        setIsOpen(false);
        containerRef.current?.focus();
        break;

      case KEYS.ARROW_UP:
        event.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
        } else {
          setFocusedIndex(prev => Math.max(0, prev - 1));
        }
        break;

      case KEYS.ARROW_DOWN:
        event.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
        } else {
          setFocusedIndex(prev => Math.min(filteredOptions.length - 1, prev + 1));
        }
        break;

      case KEYS.HOME:
        event.preventDefault();
        setFocusedIndex(0);
        break;

      case KEYS.END:
        event.preventDefault();
        setFocusedIndex(filteredOptions.length - 1);
        break;

      default:
        // Type-ahead functionality
        if (event.key.length === 1) {
          clearTimeout(typeaheadTimeoutRef.current);
          const newBuffer = typeaheadBuffer + event.key;
          setTypeaheadBuffer(newBuffer);

          const matchingIndex = filteredOptions.findIndex(option =>
            option.label.toLowerCase().startsWith(newBuffer.toLowerCase())
          );

          if (matchingIndex >= 0) {
            setFocusedIndex(matchingIndex);
          }

          typeaheadTimeoutRef.current = setTimeout(() => {
            setTypeaheadBuffer('');
          }, TYPEAHEAD_TIMEOUT);
        }
        break;
    }
  }, [disabled, isOpen, focusedIndex, filteredOptions, typeaheadBuffer]);

  // Handle option selection
  const handleOptionSelect = useCallback((option: SelectOption) => {
    if (disabled || option.disabled) return;

    if (multiple) {
      const newValue = Array.isArray(value) ? value : [];
      const optionIndex = newValue.indexOf(option.value);

      if (optionIndex === -1) {
        onChange([...newValue, option.value]);
      } else {
        onChange(newValue.filter((_, index) => index !== optionIndex));
      }
    } else {
      onChange(option.value);
      setIsOpen(false);
    }
  }, [disabled, multiple, value, onChange]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Scroll focused option into view
  useEffect(() => {
    if (isOpen && focusedIndex >= 0 && listboxRef.current) {
      const option = listboxRef.current.children[focusedIndex] as HTMLElement;
      if (option) {
        option.scrollIntoView({ block: 'nearest' });
      }
    }
  }, [focusedIndex, isOpen]);

  return (
    <div
      ref={containerRef}
      className={cn(
        'relative w-full',
        disabled && 'opacity-50 cursor-not-allowed',
        error && 'border-red-500',
        className
      )}
      onKeyDown={handleKeyDown}
      tabIndex={disabled ? -1 : 0}
      role="combobox"
      aria-expanded={isOpen}
      aria-haspopup="listbox"
      aria-disabled={disabled}
      aria-invalid={!!error}
    >
      <div
        className={cn(
          'flex items-center justify-between p-2 border rounded-md',
          isOpen && 'border-primary ring-2 ring-primary/20',
          error && 'border-red-500'
        )}
        onClick={() => !disabled && setIsOpen(!isOpen)}
      >
        <span className="truncate">{getDisplayValue()}</span>
        <svg
          className={cn(
            'w-4 h-4 transition-transform',
            isOpen && 'transform rotate-180'
          )}
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fillRule="evenodd"
            d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
            clipRule="evenodd"
          />
        </svg>
      </div>

      {isOpen && (
        <div
          className="absolute z-50 w-full mt-1 bg-background border rounded-md shadow-lg"
          style={{ maxHeight }}
        >
          {searchable && (
            <div className="p-2 border-b">
              <input
                ref={searchInputRef}
                type="text"
                className="w-full p-1 border rounded"
                placeholder="Search..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                onClick={e => e.stopPropagation()}
              />
            </div>
          )}

          {loading ? (
            <div className="p-4 text-center">Loading...</div>
          ) : (
            <ul
              ref={listboxRef}
              className="overflow-auto"
              role="listbox"
              aria-multiselectable={multiple}
              style={{ maxHeight: maxHeight - (searchable ? 57 : 0) }}
            >
              {virtualize ? (
                <div
                  style={{
                    height: virtualizer.getTotalSize(),
                    position: 'relative',
                  }}
                >
                  {virtualizer.getVirtualItems().map(virtualRow => (
                    <div
                      key={virtualRow.index}
                      style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        width: '100%',
                        height: OPTION_HEIGHT,
                        transform: `translateY(${virtualRow.start}px)`,
                      }}
                    >
                      {renderOption(filteredOptions[virtualRow.index], virtualRow.index)}
                    </div>
                  ))}
                </div>
              ) : (
                filteredOptions.map((option, index) => renderOption(option, index))
              )}
            </ul>
          )}
        </div>
      )}

      {error && (
        <div className="mt-1 text-sm text-red-500" role="alert">
          {error}
        </div>
      )}
    </div>
  );

  function renderOption(option: SelectOption, index: number) {
    const isSelected = multiple
      ? Array.isArray(value) && value.includes(option.value)
      : option.value === value;

    return (
      <li
        key={option.value}
        className={cn(
          'px-3 py-2 cursor-pointer select-none',
          isSelected && 'bg-primary text-primary-foreground',
          focusedIndex === index && 'bg-accent',
          option.disabled && 'opacity-50 cursor-not-allowed'
        )}
        role="option"
        aria-selected={isSelected}
        aria-disabled={option.disabled}
        onClick={() => handleOptionSelect(option)}
      >
        {multiple && (
          <input
            type="checkbox"
            checked={isSelected}
            onChange={() => {}}
            className="mr-2"
          />
        )}
        {option.label}
      </li>
    );
  }
};

export default Select;