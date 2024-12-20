/**
 * @file Dropdown Component
 * @version 1.0.0
 * @description A comprehensive dropdown component implementing the design system's dropdown menu pattern 
 * with enhanced accessibility, keyboard navigation, and theme integration.
 */

import React, { useCallback, useEffect, useRef, useState } from 'react'; // ^18.0.0
import { cn } from 'class-variance-authority'; // ^0.7.0
import { ChevronDown } from 'lucide-react'; // ^0.284.0
import { useVirtualizer } from '@tanstack/react-virtual'; // ^3.0.0

import { theme } from '../../config/theme';
import type { SelectOption } from '../../types/common';

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

const TYPEAHEAD_TIMEOUT = 1000;
const VIRTUAL_ROW_HEIGHT = 40;

interface DropdownProps {
  options: SelectOption[];
  value: string | string[] | number | number[];
  onChange: (value: string | string[] | number | number[]) => void;
  placeholder?: string;
  disabled?: boolean;
  error?: string;
  multiple?: boolean;
  className?: string;
  maxHeight?: number;
  virtualScroll?: boolean;
  groupBy?: string;
  loading?: boolean;
  searchable?: boolean;
  onBlur?: () => void;
  onFocus?: () => void;
}

export const Dropdown: React.FC<DropdownProps> = ({
  options,
  value,
  onChange,
  placeholder = 'Select an option',
  disabled = false,
  error,
  multiple = false,
  className,
  maxHeight = 300,
  virtualScroll = true,
  groupBy,
  loading = false,
  searchable = false,
  onBlur,
  onFocus,
}) => {
  // State management
  const [isOpen, setIsOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const [searchQuery, setSearchQuery] = useState('');
  const [typeaheadTimeout, setTypeaheadTimeout] = useState<NodeJS.Timeout>();

  // Refs for DOM elements
  const containerRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Virtual scrolling setup
  const virtualizer = useVirtualizer({
    count: options.length,
    getScrollElement: () => listRef.current,
    estimateSize: () => VIRTUAL_ROW_HEIGHT,
    overscan: 5,
  });

  // Convert value to array for consistent handling
  const selectedValues = Array.isArray(value) ? value : [value];

  // Filter and group options
  const filteredOptions = options.filter(option => 
    searchable && searchQuery
      ? option.label.toLowerCase().includes(searchQuery.toLowerCase())
      : true
  );

  const groupedOptions = groupBy
    ? filteredOptions.reduce((acc, option) => {
        const group = option[groupBy as keyof SelectOption] as string || 'Other';
        return {
          ...acc,
          [group]: [...(acc[group] || []), option],
        };
      }, {} as Record<string, SelectOption[]>)
    : { ungrouped: filteredOptions };

  // Keyboard navigation handler
  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (disabled) return;

    switch (event.key) {
      case KEYS.ENTER:
      case KEYS.SPACE:
        if (!isOpen) {
          setIsOpen(true);
          event.preventDefault();
        } else if (highlightedIndex >= 0) {
          const option = filteredOptions[highlightedIndex];
          handleOptionSelect(option);
          event.preventDefault();
        }
        break;

      case KEYS.ESCAPE:
        setIsOpen(false);
        buttonRef.current?.focus();
        event.preventDefault();
        break;

      case KEYS.ARROW_UP:
        event.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
        } else {
          setHighlightedIndex(prev => 
            prev <= 0 ? filteredOptions.length - 1 : prev - 1
          );
        }
        break;

      case KEYS.ARROW_DOWN:
        event.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
        } else {
          setHighlightedIndex(prev => 
            prev === filteredOptions.length - 1 ? 0 : prev + 1
          );
        }
        break;

      case KEYS.HOME:
        if (isOpen) {
          setHighlightedIndex(0);
          event.preventDefault();
        }
        break;

      case KEYS.END:
        if (isOpen) {
          setHighlightedIndex(filteredOptions.length - 1);
          event.preventDefault();
        }
        break;

      default:
        // Type-ahead search
        if (searchable && event.key.length === 1) {
          clearTimeout(typeaheadTimeout);
          setSearchQuery(prev => prev + event.key);
          const newTimeout = setTimeout(() => setSearchQuery(''), TYPEAHEAD_TIMEOUT);
          setTypeaheadTimeout(newTimeout);
        }
        break;
    }
  }, [isOpen, highlightedIndex, filteredOptions, disabled, searchable, typeaheadTimeout]);

  // Option selection handler
  const handleOptionSelect = useCallback((option: SelectOption) => {
    if (option.disabled) return;

    if (multiple) {
      const newValue = selectedValues.includes(option.value)
        ? selectedValues.filter(v => v !== option.value)
        : [...selectedValues, option.value];
      onChange(newValue);
    } else {
      onChange(option.value);
      setIsOpen(false);
    }

    if (!multiple) {
      buttonRef.current?.focus();
    }
  }, [multiple, onChange, selectedValues]);

  // Click outside handler
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // ARIA attributes
  const ariaProps = {
    role: 'combobox',
    'aria-expanded': isOpen,
    'aria-haspopup': 'listbox',
    'aria-controls': 'dropdown-list',
    'aria-labelledby': 'dropdown-label',
    'aria-invalid': !!error,
    'aria-disabled': disabled,
  };

  return (
    <div
      ref={containerRef}
      className={cn(
        'relative w-full',
        disabled && 'opacity-50 cursor-not-allowed',
        className
      )}
      onKeyDown={handleKeyDown}
    >
      <button
        ref={buttonRef}
        className={cn(
          'w-full px-4 py-2 text-left border rounded-md',
          'focus:outline-none focus:ring-2',
          'transition-colors duration-200',
          error
            ? 'border-red-500 focus:ring-red-500'
            : 'border-gray-300 focus:ring-primary-500',
          isOpen && 'ring-2 ring-primary-500'
        )}
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        {...ariaProps}
        onFocus={onFocus}
        onBlur={onBlur}
      >
        <span className="flex items-center justify-between">
          <span className="truncate">
            {selectedValues.length > 0
              ? options
                  .filter(opt => selectedValues.includes(opt.value))
                  .map(opt => opt.label)
                  .join(', ')
              : placeholder}
          </span>
          <ChevronDown
            className={cn(
              'w-4 h-4 transition-transform',
              isOpen && 'transform rotate-180'
            )}
          />
        </span>
      </button>

      {error && (
        <p className="mt-1 text-sm text-red-500" role="alert">
          {error}
        </p>
      )}

      {isOpen && (
        <div
          className={cn(
            'absolute z-50 w-full mt-1',
            'bg-white border border-gray-300 rounded-md shadow-lg',
            'dark:bg-gray-800 dark:border-gray-700'
          )}
          style={{ maxHeight }}
        >
          {searchable && (
            <div className="p-2 border-b border-gray-200 dark:border-gray-700">
              <input
                ref={searchInputRef}
                type="text"
                className={cn(
                  'w-full px-3 py-2 text-sm',
                  'border border-gray-300 rounded-md',
                  'focus:outline-none focus:ring-2 focus:ring-primary-500',
                  'dark:bg-gray-700 dark:border-gray-600'
                )}
                placeholder="Search options..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
              />
            </div>
          )}

          <ul
            ref={listRef}
            className="overflow-auto"
            role="listbox"
            aria-multiselectable={multiple}
            id="dropdown-list"
            style={{ maxHeight: maxHeight - (searchable ? 57 : 0) }}
          >
            {loading ? (
              <li className="px-4 py-2 text-center text-gray-500">Loading...</li>
            ) : filteredOptions.length === 0 ? (
              <li className="px-4 py-2 text-center text-gray-500">No options available</li>
            ) : (
              virtualScroll ? (
                <div
                  style={{
                    height: `${virtualizer.getTotalSize()}px`,
                    position: 'relative',
                  }}
                >
                  {virtualizer.getVirtualItems().map(virtualRow => {
                    const option = filteredOptions[virtualRow.index];
                    return (
                      <div
                        key={virtualRow.index}
                        data-index={virtualRow.index}
                        ref={virtualizer.measureElement}
                        style={{
                          position: 'absolute',
                          top: 0,
                          left: 0,
                          width: '100%',
                          transform: `translateY(${virtualRow.start}px)`,
                        }}
                      >
                        <OptionItem
                          option={option}
                          selected={selectedValues.includes(option.value)}
                          highlighted={highlightedIndex === virtualRow.index}
                          onSelect={handleOptionSelect}
                        />
                      </div>
                    );
                  })}
                </div>
              ) : (
                Object.entries(groupedOptions).map(([group, groupOptions]) => (
                  <React.Fragment key={group}>
                    {groupBy && (
                      <li className="px-4 py-2 text-sm font-semibold text-gray-500 bg-gray-50">
                        {group}
                      </li>
                    )}
                    {groupOptions.map((option, index) => (
                      <OptionItem
                        key={option.value}
                        option={option}
                        selected={selectedValues.includes(option.value)}
                        highlighted={highlightedIndex === index}
                        onSelect={handleOptionSelect}
                      />
                    ))}
                  </React.Fragment>
                ))
              )
            )}
          </ul>
        </div>
      )}
    </div>
  );
};

interface OptionItemProps {
  option: SelectOption;
  selected: boolean;
  highlighted: boolean;
  onSelect: (option: SelectOption) => void;
}

const OptionItem: React.FC<OptionItemProps> = ({
  option,
  selected,
  highlighted,
  onSelect,
}) => (
  <li
    className={cn(
      'px-4 py-2 cursor-pointer',
      'hover:bg-gray-100 dark:hover:bg-gray-700',
      'transition-colors duration-150',
      highlighted && 'bg-gray-100 dark:bg-gray-700',
      selected && 'bg-primary-50 dark:bg-primary-900',
      option.disabled && 'opacity-50 cursor-not-allowed'
    )}
    role="option"
    aria-selected={selected}
    aria-disabled={option.disabled}
    onClick={() => onSelect(option)}
  >
    <span className="flex items-center">
      {multiple && (
        <input
          type="checkbox"
          className="mr-2"
          checked={selected}
          onChange={() => {}}
          disabled={option.disabled}
        />
      )}
      {option.label}
    </span>
  </li>
);

export default Dropdown;