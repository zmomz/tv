import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import SystemLogs from './SystemLogs';
import { ThemeProvider } from '@mui/material/styles';
import theme from '../../theme/theme';
import { api } from '../../services/api';

jest.mock('../../services/api', () => ({
  api: {
    get: jest.fn(),
  },
}));

describe('SystemLogs Component', () => {
  const mockLogs = [
    {
      id: '1',
      timestamp: '2025-11-12T10:00:00Z',
      level: 'INFO',
      message: 'Application started successfully.',
      source: 'backend',
    },
    {
      id: '2',
      timestamp: '2025-11-12T10:01:00Z',
      level: 'WARNING',
      message: 'High CPU usage detected.',
      source: 'system',
    },
    {
      id: '3',
      timestamp: '2025-11-12T10:02:00Z',
      level: 'ERROR',
      message: 'Database connection failed.',
      source: 'backend',
    },
  ];

  beforeEach(() => {
    api.get.mockClear();
  });

  test('renders loading state initially', () => {
    api.get.mockReturnValueOnce(new Promise(() => {})); // Never resolve to keep it in loading state

    render(
      <ThemeProvider theme={theme}>
        <SystemLogs />
      </ThemeProvider>
    );
    expect(screen.getByText(/loading logs.../i)).toBeInTheDocument();
  });

  test('renders logs in a table after loading', async () => {
    api.get.mockResolvedValueOnce({ data: mockLogs });

    render(
      <ThemeProvider theme={theme}>
        <SystemLogs />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Timestamp')).toBeInTheDocument();
    });
    expect(screen.getByText('Level')).toBeInTheDocument();
    expect(screen.getByText('Message')).toBeInTheDocument();
    expect(screen.getByText('Source')).toBeInTheDocument();

    expect(screen.getByText('2025-11-12T10:00:00Z')).toBeInTheDocument();
    expect(screen.getByText('INFO')).toBeInTheDocument();
    expect(screen.getByText('Application started successfully.')).toBeInTheDocument();
    expect(screen.getAllByText('backend').length).toBe(2);

    expect(screen.getByText('2025-11-12T10:01:00Z')).toBeInTheDocument();
    expect(screen.getByText('WARNING')).toBeInTheDocument();
    expect(screen.getByText('High CPU usage detected.')).toBeInTheDocument();
    expect(screen.getByText('system')).toBeInTheDocument();

    expect(screen.getByText('2025-11-12T10:02:00Z')).toBeInTheDocument();
    expect(screen.getByText('ERROR')).toBeInTheDocument();
    expect(screen.getByText('Database connection failed.')).toBeInTheDocument();

    expect(api.get).toHaveBeenCalledWith('/logs');
  });

  test('renders no logs message if array is empty', async () => {
    api.get.mockResolvedValueOnce({ data: [] });

    render(
      <ThemeProvider theme={theme}>
        <SystemLogs />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/no system logs to display/i)).toBeInTheDocument();
    });
    expect(api.get).toHaveBeenCalledWith('/logs');
  });

  test('renders error message if fetching logs fails', async () => {
    const errorMessage = 'Failed to fetch logs';
    api.get.mockRejectedValueOnce(new Error(errorMessage));

    render(
      <ThemeProvider theme={theme}>
        <SystemLogs />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(`Error: ${errorMessage}`)).toBeInTheDocument();
    });
    expect(api.get).toHaveBeenCalledWith('/logs');
  });
});
