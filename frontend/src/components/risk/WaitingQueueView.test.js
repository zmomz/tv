import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import WaitingQueueView from './WaitingQueueView';
import { ThemeProvider } from '@mui/material/styles';
import theme from '../../theme/theme';
import { api } from '../../services/api';

jest.mock('../../services/api', () => ({
  api: {
    get: jest.fn(),
  },
}));

describe('WaitingQueueView Component', () => {
  const mockQueueEntries = [
    {
      id: '1',
      symbol: 'BTC/USDT',
      timeframe: '1h',
      replacement_count: 2,
      expected_profit: 50.0,
      time_in_queue: '1h 15m',
      priority_rank: 1,
    },
    {
      id: '2',
      symbol: 'ETH/USDT',
      timeframe: '4h',
      replacement_count: 0,
      expected_profit: 20.0,
      time_in_queue: '0h 45m',
      priority_rank: 2,
    },
  ];

  beforeEach(() => {
    api.get.mockClear();
  });

  test('renders loading state initially', () => {
    api.get.mockReturnValueOnce(new Promise(() => {})); // Never resolve to keep it in loading state

    render(
      <ThemeProvider theme={theme}>
        <WaitingQueueView />
      </ThemeProvider>
    );
    expect(screen.getByText(/loading.../i)).toBeInTheDocument();
  });

  test('renders queue entries in a table after loading', async () => {
    api.get.mockResolvedValueOnce({ data: mockQueueEntries });

    render(
      <ThemeProvider theme={theme}>
        <WaitingQueueView />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Symbol')).toBeInTheDocument();
    });
    expect(screen.getByText('Timeframe')).toBeInTheDocument();
    expect(screen.getByText('Replacement Count')).toBeInTheDocument();
    expect(screen.getByText('Expected Profit')).toBeInTheDocument();
    expect(screen.getByText('Time in Queue')).toBeInTheDocument();
    expect(screen.getByText('Priority Rank')).toBeInTheDocument();

    expect(screen.getByText('BTC/USDT')).toBeInTheDocument();
    expect(screen.getByText('1h')).toBeInTheDocument();
    expect(screen.getAllByText('2')[0]).toBeInTheDocument(); // Replacement Count for BTC/USDT
    expect(screen.getByText('50')).toBeInTheDocument();
    expect(screen.getByText('1h 15m')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();

    expect(screen.getByText('ETH/USDT')).toBeInTheDocument();
    expect(screen.getByText('4h')).toBeInTheDocument();
    expect(screen.getByText('0')).toBeInTheDocument();
    expect(screen.getByText('20')).toBeInTheDocument();
    expect(screen.getByText('0h 45m')).toBeInTheDocument();
    expect(screen.getAllByText('2')[1]).toBeInTheDocument(); // Priority Rank for ETH/USDT

    expect(api.get).toHaveBeenCalledWith('/queue/entries');
  });

  test('renders no queue entries message if array is empty', async () => {
    api.get.mockResolvedValueOnce({ data: [] });

    render(
      <ThemeProvider theme={theme}>
        <WaitingQueueView />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/no queued signals to display/i)).toBeInTheDocument();
    });
    expect(api.get).toHaveBeenCalledWith('/queue/entries');
  });

  test('renders error message if fetching queue entries fails', async () => {
    const errorMessage = 'Failed to fetch queue entries';
    api.get.mockRejectedValueOnce(new Error(errorMessage));

    render(
      <ThemeProvider theme={theme}>
        <WaitingQueueView />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(`Error: ${errorMessage}`)).toBeInTheDocument();
    });
    expect(api.get).toHaveBeenCalledWith('/queue/entries');
  });
});
