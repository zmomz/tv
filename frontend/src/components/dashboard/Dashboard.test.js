import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import Dashboard from './Dashboard';
import { ThemeProvider } from '@mui/material/styles';
import theme from '../../theme/theme';
import { api } from '../../services/api';

// Mock the api service
jest.mock('../../services/api', () => ({
  api: {
    get: jest.fn(),
  },
}));

describe('Dashboard Component', () => {
  const mockHealth = { status: 'ok', database: 'connected', redis: 'connected' };
  const mockStats = {
    open_positions: 5,
    total_positions: 10,
    pnl: 123.45,
  };

  beforeEach(() => {
    // Reset mocks before each test
    api.get.mockClear();
  });

  test('renders loading state initially', () => {
    api.get.mockReturnValueOnce(new Promise(() => {})); // Never resolve to keep it in loading state

    render(
      <ThemeProvider theme={theme}>
        <Dashboard health={mockHealth} />
      </ThemeProvider>
    );
    expect(screen.getByText(/loading.../i)).toBeInTheDocument();
  });

  test('renders dashboard statistics after loading', async () => {
    api.get.mockResolvedValueOnce({ data: mockStats });

    render(
      <ThemeProvider theme={theme}>
        <Dashboard health={mockHealth} />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Open Positions')).toBeInTheDocument();
      expect(screen.getByText(`${mockStats.open_positions}`)).toBeInTheDocument();
    });
    expect(screen.getByText('Total Positions')).toBeInTheDocument();
    expect(screen.getByText(`${mockStats.total_positions}`)).toBeInTheDocument();
    expect(screen.getByText('PnL')).toBeInTheDocument();
    expect(screen.getByText(`${mockStats.pnl}`)).toBeInTheDocument();
    expect(api.get).toHaveBeenCalledWith('/dashboard/stats');
  });

  test('renders error message if fetching stats fails', async () => {
    const errorMessage = 'Failed to fetch dashboard stats';
    api.get.mockRejectedValueOnce(new Error(errorMessage));

    render(
      <ThemeProvider theme={theme}>
        <Dashboard health={mockHealth} />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(`Error: ${errorMessage}`)).toBeInTheDocument();
    });
    expect(api.get).toHaveBeenCalledWith('/dashboard/stats');
  });

  test('renders system health information', async () => {
    api.get.mockResolvedValueOnce({ data: mockStats });

    render(
      <ThemeProvider theme={theme}>
        <Dashboard health={mockHealth} />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(`Database: ${mockHealth.database}`)).toBeInTheDocument();
    });
    expect(screen.getByText(`Redis: ${mockHealth.redis}`)).toBeInTheDocument();
    expect(screen.getByText(`Backend Status: ${mockHealth.status}`)).toBeInTheDocument();
  });
});
