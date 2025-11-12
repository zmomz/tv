import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import PositionsPage from '../../pages/positions/PositionsPage';
import { ThemeProvider } from '@mui/material/styles';
import theme from '../../theme/theme';
import { api } from '../../services/api';

// Mock the inner PositionRow component to avoid creating a separate test file for it
jest.mock('../../components/positions/PositionRow', () => (props) => (
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

// Mock the api service
jest.mock('../../services/api', () => ({
  api: {
    get: jest.fn(),
  },
}));

describe('PositionsPage Component', () => {
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

  beforeEach(() => {
    api.get.mockClear();
  });

  const renderWithProviders = () => {
    return render(
      <ThemeProvider theme={theme}>
        <PositionsPage />
      </ThemeProvider>
    );
  };

  test('renders loading state initially', () => {
    api.get.mockReturnValueOnce(new Promise(() => {})); // Never resolve
    renderWithProviders();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
    expect(screen.getByText(/loading.../i)).toBeInTheDocument();
  });

  test('renders positions data in a table after loading', async () => {
    api.get.mockResolvedValueOnce({ data: mockPositions });
    renderWithProviders();

    await waitFor(() => {
      expect(screen.getByText('Symbol')).toBeInTheDocument();
      expect(screen.getByText('Status')).toBeInTheDocument();
      expect(screen.getByText('Entry Price')).toBeInTheDocument();
      expect(screen.getByText('Current Price')).toBeInTheDocument();
      expect(screen.getByText('PnL')).toBeInTheDocument();
    });

    expect(screen.getByText('BTC/USDT')).toBeInTheDocument();
    expect(screen.getByText('ETH/USDT')).toBeInTheDocument();
    expect(api.get).toHaveBeenCalledWith('/positions');
  });

  test('renders no positions message if array is empty', async () => {
    api.get.mockResolvedValueOnce({ data: [] });
    renderWithProviders();
    expect(await screen.findByText(/no positions to display/i)).toBeInTheDocument();
  });

  test('renders error message if fetching positions fails', async () => {
    const errorMessage = 'Failed to fetch positions';
    api.get.mockRejectedValueOnce(new Error(errorMessage));
    renderWithProviders();
    expect(await screen.findByText(`Error: ${errorMessage}`)).toBeInTheDocument();
  });
});
