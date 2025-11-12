import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import Positions from './Positions';
import { ThemeProvider } from '@mui/material/styles';
import theme from '../../theme/theme';

describe('Positions Component', () => {
  const mockPositions = [
    {
      id: '1',
      symbol: 'BTC/USDT',
      status: 'open',
      entry_price: 30000,
      current_price: 31000,
      pnl: 1000,
    },
    {
      id: '2',
      symbol: 'ETH/USDT',
      status: 'closed',
      entry_price: 2000,
      current_price: 2100,
      pnl: 100,
    },
  ];

  test('renders loading state if positions are null', () => {
    render(
      <ThemeProvider theme={theme}>
        <Positions positions={null} />
      </ThemeProvider>
    );
    expect(screen.getByText(/loading.../i)).toBeInTheDocument();
  });

  test('renders positions data in a table', () => {
    render(
      <ThemeProvider theme={theme}>
        <Positions positions={mockPositions} />
      </ThemeProvider>
    );

    expect(screen.getByText('Symbol')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
    expect(screen.getByText('Entry Price')).toBeInTheDocument();
    expect(screen.getByText('Current Price')).toBeInTheDocument();
    expect(screen.getByText('PnL')).toBeInTheDocument();

    expect(screen.getByText('BTC/USDT')).toBeInTheDocument();
    expect(screen.getByText('open')).toBeInTheDocument();
    expect(screen.getByText('30000')).toBeInTheDocument();
    expect(screen.getByText('31000')).toBeInTheDocument();
    expect(screen.getByText('1000')).toBeInTheDocument();

    expect(screen.getByText('ETH/USDT')).toBeInTheDocument();
    expect(screen.getByText('closed')).toBeInTheDocument();
    expect(screen.getByText('2000')).toBeInTheDocument();
    expect(screen.getByText('2100')).toBeInTheDocument();
    expect(screen.getByText('100')).toBeInTheDocument();
  });

  test('renders no positions message if array is empty', () => {
    render(
      <ThemeProvider theme={theme}>
        <Positions positions={[]} />
      </ThemeProvider>
    );
    expect(screen.getByText(/no positions to display/i)).toBeInTheDocument();
  });
});
