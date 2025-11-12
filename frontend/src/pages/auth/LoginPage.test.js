// Mock react-router-dom's useNavigate and Link
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: jest.fn(),
  Link: ({ children, to }) => <a href={to}>{children}</a>,
}));

// Mock the useAuth hook
jest.mock('../../hooks/useAuth', () => ({
  useAuth: jest.fn(),
}));

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter as Router } from 'react-router-dom';
import LoginPage from '../../pages/auth/LoginPage';
import { useAuth } from '../../hooks/useAuth';

describe('LoginPage Component', () => {
  const mockLogin = jest.fn();
  const mockNavigate = jest.fn();

  beforeEach(() => {
    useAuth.mockReturnValue({ login: mockLogin });
    require('react-router-dom').useNavigate.mockReturnValue(mockNavigate);
    mockLogin.mockClear();
    mockNavigate.mockClear();
  });

  const renderWithRouter = () => {
    return render(
      <Router>
        <LoginPage />
      </Router>
    );
  };

  test('renders email and password inputs', () => {
    renderWithRouter();
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });

  test('allows typing in email and password fields', () => {
    renderWithRouter();
    const emailInput = screen.getByLabelText(/email address/i);
    const passwordInput = screen.getByLabelText(/password/i);

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });

    expect(emailInput.value).toBe('test@example.com');
    expect(passwordInput.value).toBe('password123');
  });

  test('calls login and navigates on successful submission', async () => {
    mockLogin.mockResolvedValueOnce();
    renderWithRouter();
    
    const emailInput = screen.getByLabelText(/email address/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const loginButton = screen.getByRole('button', { name: /login/i });

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('test@example.com', 'password123');
    });
    expect(mockNavigate).toHaveBeenCalledWith('/');
  });

  test('displays error message on failed login', async () => {
    const errorMessage = 'Invalid credentials';
    mockLogin.mockRejectedValueOnce({ response: { data: { detail: errorMessage } } });
    renderWithRouter();

    const emailInput = screen.getByLabelText(/email address/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const loginButton = screen.getByRole('button', { name: /login/i });

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } });
    fireEvent.click(loginButton);

    expect(await screen.findByText(errorMessage)).toBeInTheDocument();
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  test('displays error message if fields are empty', async () => {
    renderWithRouter();
    const loginButton = screen.getByRole('button', { name: /login/i });
    fireEvent.click(loginButton);

    expect(await screen.findByText('Both email and password are required.')).toBeInTheDocument();
    expect(mockLogin).not.toHaveBeenCalled();
  });
});