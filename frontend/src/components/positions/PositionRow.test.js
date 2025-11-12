import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import PositionRow from './PositionRow';
import { ThemeProvider } from '@mui/material/styles';
import theme from '../../theme/theme';

describe('PositionRow Component', () => {
  const mockPosition = {
    id: '1',
    symbol: 'BTC/USDT',
    status: 'open',
    entry_price: 30000,
    current_price: 31000,
    pnl: 1000,
    dca_orders: [
      { id: 'dca1', filled_price: 30000, capital_weight: 0.5, tp_target: 31000, status: 'filled' },
      { id: 'dca2', filled_price: null, capital_weight: 0.5, tp_target: 30500, status: 'pending' },
    ],
  };

  test('renders position details correctly', () => {
    render(
      <ThemeProvider theme={theme}>
        <table>
          <tbody>
            <PositionRow row={mockPosition} />
          </tbody>
        </table>
      </ThemeProvider>
    );

    expect(screen.getByText('BTC/USDT')).toBeInTheDocument();
    expect(screen.getByText('open')).toBeInTheDocument();
    expect(screen.getByText('30000')).toBeInTheDocument();
    expect(screen.getByText('31000')).toBeInTheDocument();
    expect(screen.getByText('1000')).toBeInTheDocument();
  });

  test('expands and collapses to show DCA legs', async () => {
    render(
      <ThemeProvider theme={theme}>
        <table>
          <tbody>
            <PositionRow row={mockPosition} />
          </tbody>
        </table>
      </ThemeProvider>
    );

    // DCA legs should not be visible initially
    expect(screen.queryByText('DCA Legs')).not.toBeInTheDocument();

    // Click the expand button
    fireEvent.click(screen.getByLabelText('expand row'));

    // DCA legs should now be visible
    expect(screen.getByText('DCA Legs')).toBeInTheDocument();
    expect(screen.getByText('Filled Price')).toBeInTheDocument();
    expect(screen.getByText('Capital Weight')).toBeInTheDocument();
    expect(screen.getByText('TP Target')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();

    expect(screen.getAllByText('30000')[1]).toBeInTheDocument(); // Filled Price for dca1
    expect(screen.getAllByText('0.5')[0]).toBeInTheDocument(); // Capital Weight for dca1
    expect(screen.getAllByText('31000')[1]).toBeInTheDocument(); // TP Target for dca1
    expect(screen.getByText('filled')).toBeInTheDocument(); // Status for dca1

    expect(screen.getByText('pending')).toBeInTheDocument(); // Status for dca2

    // Click the collapse button
    fireEvent.click(screen.getByLabelText('expand row'));

    await waitFor(() => expect(screen.queryByText('DCA Legs')).not.toBeInTheDocument());
  });

  test('renders correctly when dca_orders is empty', () => {
    const positionWithoutDCA = { ...mockPosition, dca_orders: [] };
    render(
      <ThemeProvider theme={theme}>
        <table>
          <tbody>
            <PositionRow row={positionWithoutDCA} />
          </tbody>
        </table>
      </ThemeProvider>
    );

    fireEvent.click(screen.getByLabelText('expand row'));
    expect(screen.getByText('DCA Legs')).toBeInTheDocument();
    expect(screen.queryByText('0.5')).not.toBeInTheDocument(); // No capital weight from DCA orders
  });
});
