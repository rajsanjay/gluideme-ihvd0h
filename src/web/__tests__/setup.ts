import '@testing-library/jest-dom/extend-expect'; // v5.16.5
import { vi } from 'vitest'; // v0.34.0
import { render, screen } from '@testing-library/react'; // v14.0.0
import { toHaveNoViolations, configureAxe } from 'jest-axe'; // v8.0.0

// Extend Jest matchers with accessibility testing
expect.extend(toHaveNoViolations);

// Configure axe-core with WCAG 2.1 AA standards
configureAxe({
  rules: {
    'wcag2a': { enabled: true },
    'wcag2aa': { enabled: true },
    'wcag21a': { enabled: true },
    'wcag21aa': { enabled: true }
  }
});

// Enhanced IntersectionObserver Mock Implementation
class IntersectionObserverMock {
  private entries: IntersectionObserverEntry[] = [];
  private callback: IntersectionObserverCallback;
  private options: IntersectionObserverInit;
  private elementStates: Map<Element, boolean> = new Map();

  constructor(callback: IntersectionObserverCallback, options: IntersectionObserverInit = {}) {
    this.callback = callback;
    this.options = options;
  }

  observe(element: Element): void {
    const entry = {
      target: element,
      isIntersecting: false,
      boundingClientRect: element.getBoundingClientRect(),
      intersectionRatio: 0,
      intersectionRect: element.getBoundingClientRect(),
      rootBounds: null,
      time: Date.now()
    } as IntersectionObserverEntry;

    this.entries.push(entry);
    this.elementStates.set(element, false);
    this.callback([entry], this);
  }

  unobserve(element: Element): void {
    const index = this.entries.findIndex(entry => entry.target === element);
    if (index > -1) {
      this.entries.splice(index, 1);
      this.elementStates.delete(element);
    }
  }

  disconnect(): void {
    this.entries = [];
    this.elementStates.clear();
  }

  // Test helper to simulate intersection
  simulateIntersection(element: Element, isIntersecting: boolean): void {
    const entry = this.entries.find(entry => entry.target === element);
    if (entry) {
      const updatedEntry = {
        ...entry,
        isIntersecting,
        intersectionRatio: isIntersecting ? 1 : 0,
        time: Date.now()
      };
      this.callback([updatedEntry], this);
      this.elementStates.set(element, isIntersecting);
    }
  }
}

// Mock ResizeObserver
class ResizeObserverMock {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}

// Setup global mocks
beforeAll(() => {
  // Mock ResizeObserver
  global.ResizeObserver = ResizeObserverMock;
  
  // Mock IntersectionObserver
  global.IntersectionObserver = IntersectionObserverMock;

  // Mock matchMedia
  window.matchMedia = vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }));

  // Mock localStorage
  const localStorageMock = {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
    length: 0,
    key: vi.fn()
  };
  Object.defineProperty(window, 'localStorage', { value: localStorageMock });

  // Mock sessionStorage
  const sessionStorageMock = {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
    length: 0,
    key: vi.fn()
  };
  Object.defineProperty(window, 'sessionStorage', { value: sessionStorageMock });

  // Mock requestAnimationFrame
  window.requestAnimationFrame = vi.fn(callback => setTimeout(callback, 0));
});

// Setup component state tracking utilities
const stateTracker = {
  history: new Map<string, any[]>(),
  
  recordState(componentId: string, state: any): void {
    if (!this.history.has(componentId)) {
      this.history.set(componentId, []);
    }
    this.history.get(componentId)?.push({
      state,
      timestamp: Date.now()
    });
  },

  getStateHistory(componentId: string): any[] {
    return this.history.get(componentId) || [];
  },

  clearHistory(componentId?: string): void {
    if (componentId) {
      this.history.delete(componentId);
    } else {
      this.history.clear();
    }
  },

  validateStateTransition(componentId: string, expectedStates: any[]): boolean {
    const history = this.getStateHistory(componentId);
    const states = history.map(entry => entry.state);
    return JSON.stringify(states) === JSON.stringify(expectedStates);
  }
};

// Cleanup after each test
afterEach(() => {
  vi.clearAllMocks();
  stateTracker.clearHistory();
  localStorage.clear();
  sessionStorage.clear();
});

// Export test utilities
export {
  stateTracker,
  IntersectionObserverMock,
  ResizeObserverMock
};