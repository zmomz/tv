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
import RegisterPage from '../../pages/auth/RegisterPage';
import { useAuth } from '../../hooks/useAuth';

describe('RegisterPage Component', () => {
  const mockRegister = jest.fn();
  const mockNavigate = jest.fn();

  beforeEach(() => {
    useAuth.mockReturnValue({ register: mockRegister });
    require('react-router-dom').useNavigate.mockReturnValue(mockNavigate);
    mockRegister.mockClear();
    mockNavigate.mockClear();
  });

  const renderWithRouter = () => {
    return render(
      <Router>
        <RegisterPage />
      </Router>
    );
  };

  test('renders username, email, and password inputs', () => {
    renderWithRouter();
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });

  test('calls register and navigates on successful submission', async () => {
    mockRegister.mockResolvedValueOnce();
    renderWithRouter();
    
    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: 'testuser' } });
    fireEvent.change(screen.getByLabelText(/email address/i), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'password123' } });
    fireEvent.click(screen.getByRole('button', { name: /register/i }));

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith('testuser', 'test@example.com', 'password123');
    });
    expect(mockNavigate).toHaveBeenCalledWith('/');
  });

  test('displays error message on failed registration', async () => {
    const errorMessage = 'Username already exists';
    mockRegister.mockRejectedValueOnce({ response: { data: { detail: errorMessage } } });
    renderWithRouter();

    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: 'testuser' } });
    fireEvent.change(screen.getByLabelText(/email address/i), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'password123' } });
    fireEvent.click(screen.getByRole('button', { name: /register/i }));

    expect(await screen.findByText(errorMessage)).toBeInTheDocument();
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  test('displays error message if fields are empty', async () => {
    renderWithRouter();
    const registerButton = screen.getByRole('button', { name: /register/i });
    fireEvent.click(registerButton);

    expect(await screen.findByText('All fields are required.')).toBeInTheDocument();
    expect(mockRegister).not.toHaveBeenCalled();
  });
});