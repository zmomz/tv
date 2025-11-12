import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import SettingsPage from '../../pages/admin/SettingsPage';
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

describe('SettingsPage Component', () => {
  beforeEach(() => {
    api.get.mockClear();
    api.put.mockClear();
    api.get.mockResolvedValue({ data: mockConfig });
  });

  test('renders loading state initially', () => {
    api.get.mockReturnValueOnce(new Promise(() => {})); // Never resolve
    render(<SettingsPage />);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  test('renders settings form with initial values', async () => {
    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByLabelText('Mode')).toHaveValue('development');
    });

    expect(screen.getByLabelText('Data Directory')).toHaveValue('./data');
    expect(screen.getByLabelText('Log Level')).toHaveValue('INFO');
    expect(screen.getByLabelText('Name')).toHaveValue('binance');
    expect(screen.getByLabelText('API Key')).toHaveValue('test_key');
    expect(screen.getByLabelText('API Secret')).toHaveValue('test_secret');
    expect(screen.getByLabelText('Testnet')).toBeChecked();
    expect(screen.getByLabelText('Precision Refresh (sec)')).toHaveValue(3600);
    expect(screen.getByLabelText('Max Open Groups')).toHaveValue(5);
    expect(screen.getByLabelText('Count Pyramids Towards Pool')).toBeChecked();
    expect(screen.getByLabelText('Max Pyramids Per Group')).toHaveValue(5);
    expect(screen.getByLabelText('Max DCA Per Pyramid')).toHaveValue(7);
    expect(screen.getByLabelText('Take Profit Mode')).toHaveValue('leg');
    expect(screen.getByLabelText('Loss Threshold (%)')).toHaveValue(-10);
    expect(screen.getByLabelText('Require Full Pyramids for Activation')).not.toBeChecked();
    expect(screen.getByLabelText('Post Full Wait (min)')).toHaveValue(30);
  });

  test('updates config state on input change', async () => {
    render(<SettingsPage />);
    await screen.findByLabelText('Mode');

    const modeInput = screen.getByLabelText('Mode');
    fireEvent.change(modeInput, { target: { value: 'production' } });
    expect(modeInput.value).toBe('production');
  });

  test('submits updated config on form submission', async () => {
    render(<SettingsPage />);
    await screen.findByLabelText('Mode');

    fireEvent.change(screen.getByLabelText('Mode'), { target: { value: 'production' } });

    const saveButton = screen.getByRole('button', { name: /save settings/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(api.put).toHaveBeenCalledWith('/config', expect.objectContaining({
        app: expect.objectContaining({ mode: 'production' }),
      }));
    });

    expect(await screen.findByText('Settings saved successfully!')).toBeInTheDocument();
  });

  test('handles error on config fetch failure', async () => {
    const errorMessage = 'Failed to fetch config';
    api.get.mockRejectedValueOnce(new Error(errorMessage));
    render(<SettingsPage />);
    expect(await screen.findByText(`Failed to load settings: ${errorMessage}`)).toBeInTheDocument();
  });

  test('handles error on config save failure', async () => {
    const errorMessage = 'Failed to save settings';
    api.put.mockRejectedValueOnce(new Error(errorMessage));
    render(<SettingsPage />);
    await screen.findByLabelText('Mode');

    const saveButton = screen.getByRole('button', { name: /save settings/i });
    fireEvent.click(saveButton);

    expect(await screen.findByText(errorMessage)).toBeInTheDocument();
  });
});
