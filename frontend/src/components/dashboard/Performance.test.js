import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import Performance from './Performance';
import { ThemeProvider } from '@mui/material/styles';
import theme from '../../theme/theme';
import { api } from '../../services/api';

jest.mock('../../services/api', () => ({
  api: {
    get: jest.fn(),
  },
}));

describe('Performance Component', () => {
  const mockAnalytics = {
    total_pnl: 1500.75,
    total_roi: 15.25,
    win_rate: 60.0,
    total_trades: 100,
    winning_trades: 60,
    losing_trades: 40,
    max_drawdown: -5.5,
    equity_curve_data: [], // Mock data for chart
  };

  beforeEach(() => {
    api.get.mockClear();
    api.get.mockResolvedValue({ data: mockAnalytics });
  });

  test('renders loading state initially', () => {
    api.get.mockReturnValueOnce(new Promise(() => {})); // Never resolve to keep it in loading state

    render(
      <ThemeProvider theme={theme}>
        <Performance />
      </ThemeProvider>
    );
    expect(screen.getByText(/loading performance data.../i)).toBeInTheDocument();
  });

  test('renders performance metrics after loading', async () => {
    render(
      <ThemeProvider theme={theme}>
        <Performance />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Total PnL')).toBeInTheDocument();
    });
    expect(screen.getByText('1500.75')).toBeInTheDocument();
    expect(screen.getByText('Total ROI')).toBeInTheDocument();
    expect(screen.getByText('15.25%')).toBeInTheDocument();
    expect(screen.getByText('Win Rate')).toBeInTheDocument();
    expect(screen.getByText('60.00%')).toBeInTheDocument();
    expect(screen.getByText('Total Trades: 100')).toBeInTheDocument();
    expect(screen.getByText('Winning Trades: 60')).toBeInTheDocument();
    expect(screen.getByText('Losing Trades: 40')).toBeInTheDocument();
    expect(screen.getByText('Max Drawdown: -5.50%')).toBeInTheDocument();
    expect(screen.getByText('Equity Curve Chart Placeholder')).toBeInTheDocument();

    expect(api.get).toHaveBeenCalledWith('/analytics');
  });

  test('renders error message if fetching analytics fails', async () => {
    const errorMessage = 'Failed to fetch analytics';
    api.get.mockRejectedValueOnce(new Error(errorMessage));

    render(
      <ThemeProvider theme={theme}>
        <Performance />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(`Error: ${errorMessage}`)).toBeInTheDocument();
    });
    expect(api.get).toHaveBeenCalledWith('/analytics');
  });

  test('renders N/A for missing data', async () => {
    api.get.mockResolvedValueOnce({ data: {} }); // Empty data

    render(
      <ThemeProvider theme={theme}>
        <Performance />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Total PnL')).toBeInTheDocument();
    });
    expect(screen.getByText('N/A')).toBeInTheDocument(); // For PnL
    expect(screen.getAllByText('N/A%')[0]).toBeInTheDocument(); // For ROI
    expect(screen.getAllByText('N/A%')[1]).toBeInTheDocument(); // For Win Rate
    expect(screen.getByText('Total Trades: N/A')).toBeInTheDocument();
    expect(screen.getByText('Winning Trades: N/A')).toBeInTheDocument();
    expect(screen.getByText('Losing Trades: N/A')).toBeInTheDocument();
    expect(screen.getByText('Max Drawdown: N/A%')).toBeInTheDocument();
  });
});
