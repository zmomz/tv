// Mock react-router-dom's Link component and useNavigate
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  Link: ({ children, to }) => <a href={to}>{children}</a>,
  useNavigate: jest.fn(), // Mock useNavigate as it's used in MainLayout
}));

// Mock the useAuth hook
jest.mock('../../hooks/useAuth', () => ({
  useAuth: jest.fn(),
}));

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter as Router } from 'react-router-dom';
import MainLayout from './MainLayout';
import { ThemeProvider } from '@mui/material/styles';
import theme from '../../theme/theme';
import { useAuth } from '../../hooks/useAuth';

describe('MainLayout Component', () => {
  const mockLogout = jest.fn();

  beforeEach(() => {
    useAuth.mockReturnValue({ logout: mockLogout });
    mockLogout.mockClear();
  });

  const renderWithProviders = (children) => {
    return render(
      <ThemeProvider theme={theme}>
        <Router>
          {children}
        </Router>
      </ThemeProvider>
    );
  };

  test('renders children content', () => {
    renderWithProviders(
      <MainLayout>
        <div>Test Child Content</div>
      </MainLayout>
    );
    expect(screen.getByText('Test Child Content')).toBeInTheDocument();
  });

  test('renders navigation items', () => {
    renderWithProviders(<MainLayout />);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Positions')).toBeInTheDocument();
    expect(screen.getByText('Performance')).toBeInTheDocument();
    expect(screen.getByText('Logs')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  test('calls logout when logout button is clicked', () => {
    renderWithProviders(<MainLayout />);
    const logoutButton = screen.getByText('Logout');
    fireEvent.click(logoutButton);
    expect(mockLogout).toHaveBeenCalledTimes(1);
  });
});
