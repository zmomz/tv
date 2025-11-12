import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import Positions from './Positions';
import { ThemeProvider } from '@mui/material/styles';
import theme from '../../theme/theme';

// Mock the inner Row component to avoid creating a separate test file for it
jest.mock('./PositionRow', () => (props) => (
  <tr data-testid="position-row">
    <td>
      <button
        aria-label="expand row"
        onClick={() => props.setOpen(!props.open)}
      >
        {props.open ? 'collapse' : 'expand'}
      </button>
    </td>
    <td>{props.row.symbol}</td>
  </tr>
));


describe('Positions Component', () => {
  const mockPositions = [
    {
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
    },
    {
      id: '2',
      symbol: 'ETH/USDT',
      status: 'closed',
      entry_price: 2000,
      current_price: 2100,
      pnl: 100,
      dca_orders: [],
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
    expect(screen.getByText('ETH/USDT')).toBeInTheDocument();
  });

  test('renders no positions message if array is empty', () => {
    render(
      <ThemeProvider theme={theme}>
        <Positions positions={[]} />
      </ThemeProvider>
    );
    expect(screen.getByText(/no positions to display/i)).toBeInTheDocument();
  });

  test('does not show DCA details by default', () => {
    render(
      <ThemeProvider theme={theme}>
        <Positions positions={mockPositions} />
      </ThemeProvider>
    );
    expect(screen.queryByText('DCA Legs')).not.toBeInTheDocument();
  });
});