import React from 'react';
import { render, screen, waitFor, fireEvent, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { setupServer } from 'msw/node';
import { rest } from 'msw';
import axe from '@axe-core/react';
import DashboardPage from '../../app/dashboard/page';
import { AuthProvider } from '../../providers/auth-provider';

// Mock data for testing
const mockDashboardMetrics = {
  activeRules: 245,
  pendingReviews: 12,
  totalInstitutions: 50,
  completedTransfers: 1500,
  lastUpdated: '2023-01-01T00:00:00Z'
};

const mockRecentActivity = [
  {
    id: '1',
    institution: 'UC Berkeley',
    major: 'Computer Science',
    status: 'Active',
    updatedAt: '2023-01-01T00:00:00Z',
    type: 'major',
    version: 1
  }
];

// MSW server setup for API mocking
const server = setupServer(
  rest.get('/api/v1/requirements', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        data: mockRecentActivity,
        total: 1,
        page: 1,
        pageSize: 10
      })
    );
  }),
  rest.get('/api/v1/metrics/dashboard', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json(mockDashboardMetrics)
    );
  })
);

// Helper function to render component with providers
const renderWithProviders = (
  ui: React.ReactNode,
  { userRole = 'admin' } = {}
) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0
      }
    }
  });

  const mockUser = {
    id: '1',
    email: 'admin@example.com',
    role: userRole,
    institutionId: null,
    preferences: {},
    lastLogin: null
  };

  return render(
    <AuthProvider initialState={{ user: mockUser, isAuthenticated: true }}>
      <QueryClientProvider client={queryClient}>
        {ui}
      </QueryClientProvider>
    </AuthProvider>
  );
};

// Helper function to measure component render performance
const measurePerformance = async (component: React.ReactNode): Promise<number> => {
  const start = performance.now();
  const { container } = renderWithProviders(component);
  await waitFor(() => {
    expect(container).toBeTruthy();
  });
  return performance.now() - start;
};

describe('DashboardPage', () => {
  beforeEach(() => {
    server.listen();
    vi.useFakeTimers();
  });

  afterEach(() => {
    server.resetHandlers();
    vi.clearAllTimers();
  });

  afterAll(() => {
    server.close();
    vi.useRealTimers();
  });

  it('should render without accessibility violations', async () => {
    const { container } = renderWithProviders(<DashboardPage />);
    const results = await axe(container);
    expect(results.violations).toHaveLength(0);
  });

  it('should display dashboard metrics for admin users', async () => {
    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('Active Rules')).toBeInTheDocument();
      expect(screen.getByText('245')).toBeInTheDocument();
      expect(screen.getByText('Pending Reviews')).toBeInTheDocument();
      expect(screen.getByText('12')).toBeInTheDocument();
    });
  });

  it('should restrict access to metrics for unauthorized users', async () => {
    renderWithProviders(<DashboardPage />, { userRole: 'guest' });

    await waitFor(() => {
      expect(screen.queryByText('Active Rules')).not.toBeInTheDocument();
      expect(screen.queryByText('Pending Reviews')).not.toBeInTheDocument();
    });
  });

  it('should display recent activity with proper formatting', async () => {
    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      const activityTable = screen.getByRole('grid');
      expect(activityTable).toBeInTheDocument();
      
      const row = within(activityTable).getByText('UC Berkeley');
      expect(row).toBeInTheDocument();
      
      const status = within(activityTable).getByText('Active');
      expect(status).toHaveClass('bg-green-100', 'text-green-800');
    });
  });

  it('should meet performance requirements', async () => {
    const renderTime = await measurePerformance(<DashboardPage />);
    expect(renderTime).toBeLessThan(2000); // 2s requirement from specs
  });

  it('should handle real-time updates via WebSocket', async () => {
    const mockWebSocket = {
      send: vi.fn(),
      close: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn()
    };

    // @ts-ignore - mock WebSocket
    global.WebSocket = vi.fn(() => mockWebSocket);

    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(global.WebSocket).toHaveBeenCalledWith(expect.stringContaining('ws'));
    });

    // Simulate WebSocket message
    const messageEvent = new MessageEvent('message', {
      data: JSON.stringify({
        activeRules: 246,
        pendingReviews: 13
      })
    });

    mockWebSocket.onmessage?.(messageEvent);

    await waitFor(() => {
      expect(screen.getByText('246')).toBeInTheDocument();
      expect(screen.getByText('13')).toBeInTheDocument();
    });
  });

  it('should handle error states gracefully', async () => {
    server.use(
      rest.get('/api/v1/metrics/dashboard', (req, res, ctx) => {
        return res(ctx.status(500));
      })
    );

    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText(/error occurred/i)).toBeInTheDocument();
    });
  });

  it('should update data on refresh button click', async () => {
    renderWithProviders(<DashboardPage />);

    const refreshButton = screen.getByRole('button', { name: /refresh/i });
    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(screen.getByText('245')).toBeInTheDocument();
    });
  });

  it('should preserve state during route changes', async () => {
    const { rerender } = renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('245')).toBeInTheDocument();
    });

    // Simulate route change and return
    rerender(<DashboardPage />);

    expect(screen.getByText('245')).toBeInTheDocument();
  });

  it('should handle pagination in recent activity', async () => {
    renderWithProviders(<DashboardPage />);

    const nextPageButton = await screen.findByRole('button', { name: /next/i });
    fireEvent.click(nextPageButton);

    await waitFor(() => {
      expect(screen.getByText('Page 2')).toBeInTheDocument();
    });
  });

  it('should apply correct role-based permissions', async () => {
    const { rerender } = renderWithProviders(<DashboardPage />);

    // Test admin view
    await waitFor(() => {
      expect(screen.getByText('Active Rules')).toBeInTheDocument();
    });

    // Test counselor view
    rerender(<DashboardPage userRole="counselor" />);
    await waitFor(() => {
      expect(screen.queryByText('Pending Reviews')).not.toBeInTheDocument();
    });
  });
});