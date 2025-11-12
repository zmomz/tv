import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import RiskEnginePanel from './RiskEnginePanel';
import { ThemeProvider } from '@mui/material/styles';
import theme from '../../theme/theme';
import { api } from '../../services/api';

jest.mock('../../services/api', () => ({
  api: {
    get: jest.fn(),
  },
}));

describe('RiskEnginePanel Component', () => {
  const mockRiskStats = {
    loss_percent: -5.2,
    loss_usd: 150.75,
    timer_remaining: '0h 30m',
    five_pyramids_reached: true,
    age_filter_passed: false,
    available_winning_offsets: 3,
    total_winning_profit_usd: 200.00,
    projected_plan: 'Close 2 winners for $150.75',
  };

  beforeEach(() => {
    api.get.mockClear();
  });

  test('renders loading state initially', () => {
    api.get.mockReturnValueOnce(new Promise(() => {})); // Never resolve to keep it in loading state

    render(
      <ThemeProvider theme={theme}>
        <RiskEnginePanel />
      </ThemeProvider>
    );
    expect(screen.getByText(/loading.../i)).toBeInTheDocument();
  });

  test('renders risk engine statistics after loading', async () => {
    api.get.mockResolvedValueOnce({ data: mockRiskStats });

    render(
      <ThemeProvider theme={theme}>
        <RiskEnginePanel />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(`Loss %: ${mockRiskStats.loss_percent}`)).toBeInTheDocument();
    });
    expect(screen.getByText(`Loss USD: ${mockRiskStats.loss_usd}`)).toBeInTheDocument();
    expect(screen.getByText(`Timer Remaining: ${mockRiskStats.timer_remaining}`)).toBeInTheDocument();
    expect(screen.getByText(`5 Pyramids Reached: ${mockRiskStats.five_pyramids_reached ? 'Yes' : 'No'}`)).toBeInTheDocument();
    expect(screen.getByText(`Age Filter Passed: ${mockRiskStats.age_filter_passed ? 'Yes' : 'No'}`)).toBeInTheDocument();
    expect(screen.getByText(`Available Winning Offsets: ${mockRiskStats.available_winning_offsets}`)).toBeInTheDocument();
    expect(screen.getByText(`Total Winning Profit USD: ${mockRiskStats.total_winning_profit_usd}`)).toBeInTheDocument();
    expect(screen.getByText(`Projected Plan: ${mockRiskStats.projected_plan}`)).toBeInTheDocument();
    expect(api.get).toHaveBeenCalledWith('/risk-engine/stats');
  });

  test('renders error message if fetching risk stats fails', async () => {
    const errorMessage = 'Failed to fetch risk engine stats';
    api.get.mockRejectedValueOnce(new Error(errorMessage));

    render(
      <ThemeProvider theme={theme}>
        <RiskEnginePanel />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(`Error: ${errorMessage}`)).toBeInTheDocument();
    });
    expect(api.get).toHaveBeenCalledWith('/risk-engine/stats');
  });
});
