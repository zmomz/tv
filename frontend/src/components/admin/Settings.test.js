import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import Settings from './Settings';
import { api } from '../../services/api';

// Mock the api service
jest.mock('../../services/api', () => ({
  api: {
    get: jest.fn(),
    put: jest.fn(),
  },
}));

const mockConfig = {
  app: {
    mode: 'development',
    data_dir: './data',
    log_level: 'INFO',
  },
  exchange: {
    name: 'binance',
    api_key: 'test_key',
    api_secret: 'test_secret',
    testnet: true,
    precision_refresh_sec: 3600,
  },
  execution_pool: {
    max_open_groups: 5,
    count_pyramids: true,
  },
  grid_strategy: {
    max_pyramids_per_group: 5,
    max_dca_per_pyramid: 7,
    tp_mode: 'leg',
  },
  risk_engine: {
    loss_threshold_percent: -10.0,
    require_full_pyramids: false,
    post_full_wait_minutes: 30,
  },
};

describe('Settings Component', () => {
  beforeEach(() => {
    api.get.mockClear();
    api.put.mockClear();
    api.get.mockResolvedValue({ data: mockConfig });
    jest.spyOn(window, 'alert').mockImplementation(() => {}); // Mock window.alert
  });

  afterEach(() => {
    window.alert.mockRestore(); // Restore window.alert after each test
  });

  test('renders loading state initially', () => {
    api.get.mockReturnValueOnce(new Promise(() => {})); // Never resolve to keep it in loading state

    render(<Settings />);
    expect(screen.getByText(/loading.../i)).toBeInTheDocument();
  });

  test('renders settings form with initial values', async () => {
    render(<Settings />);

    await waitFor(() => {
      expect(screen.getByLabelText('Mode:')).toHaveValue('development');
    });
    expect(screen.getByLabelText(/data directory:/i)).toHaveValue('./data');
    expect(screen.getByLabelText(/log level:/i)).toHaveValue('INFO');

    expect(screen.getByLabelText(/name:/i)).toHaveValue('binance');
    expect(screen.getByLabelText(/api key:/i)).toHaveValue('test_key');
    expect(screen.getByLabelText(/api secret:/i)).toHaveValue('test_secret');
    expect(screen.getByLabelText(/testnet:/i)).toBeChecked();
    expect(screen.getByLabelText('Precision Refresh (sec):')).toHaveValue(3600);

    expect(screen.getByLabelText(/max open groups:/i)).toHaveValue(5);
    expect(screen.getByLabelText(/count pyramids:/i)).toBeChecked();

    // New Grid Strategy fields
    expect(screen.getByLabelText(/max pyramids per group:/i)).toHaveValue(5);
    expect(screen.getByLabelText(/max dca per pyramid:/i)).toHaveValue(7);
    expect(screen.getByLabelText('TP Mode:')).toHaveValue('leg');

    expect(screen.getByLabelText('Loss Threshold (%):')).toHaveValue(-10);
    expect(screen.getByLabelText('Require Full Pyramids:')).not.toBeChecked();
    expect(screen.getByLabelText('Post Full Wait (min):')).toHaveValue(30);

    expect(api.get).toHaveBeenCalledWith('/config');
  });

  test('updates config state on input change', async () => {
    render(<Settings />);

    await waitFor(() => {
      expect(screen.getByLabelText('Mode:')).toHaveValue('development');
    });

    const modeInput = screen.getByLabelText('Mode:');
    fireEvent.change(modeInput, { target: { name: 'app.mode', value: 'production' } });
    expect(modeInput).toHaveValue('production');

    const maxPyramidsInput = screen.getByLabelText(/max pyramids per group:/i);
    fireEvent.change(maxPyramidsInput, { target: { name: 'grid_strategy.max_pyramids_per_group', value: 10 } });
    expect(maxPyramidsInput).toHaveValue(10);
  });

  test('submits updated config on form submission', async () => {
    render(<Settings />);

    await waitFor(() => {
      expect(screen.getByLabelText('Mode:')).toHaveValue('development');
    });

    const modeInput = screen.getByLabelText('Mode:');
    fireEvent.change(modeInput, { target: { name: 'app.mode', value: 'production' } });

    const maxDcaInput = screen.getByLabelText(/max dca per pyramid:/i);
    fireEvent.change(maxDcaInput, { target: { name: 'grid_strategy.max_dca_per_pyramid', value: 10 } });

    const saveButton = screen.getByRole('button', { name: /save/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(api.put).toHaveBeenCalledWith('/config', {
        ...mockConfig,
        app: { ...mockConfig.app, mode: 'production' },
        grid_strategy: { ...mockConfig.grid_strategy, max_dca_per_pyramid: 10 },
      });
    });
    expect(window.alert).toHaveBeenCalledWith('Settings saved successfully!');
  });

  test('handles error on config fetch failure', async () => {
    const errorMessage = 'Failed to fetch config';
    api.get.mockRejectedValueOnce(new Error(errorMessage));

    render(<Settings />);

    await waitFor(() => {
      expect(screen.getByText(`Error: ${errorMessage}`)).toBeInTheDocument();
    });
  });

  test('handles error on config save failure', async () => {
    api.put.mockRejectedValueOnce(new Error('Failed to save'));

    render(<Settings />);

    await waitFor(() => {
      expect(screen.getByLabelText('Mode:')).toHaveValue('development');
    });

    const saveButton = screen.getByRole('button', { name: /save/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith('Failed to save settings.');
    });
  });
});
