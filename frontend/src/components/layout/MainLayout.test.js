import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import MainLayout from './MainLayout';
import { ThemeProvider } from '@mui/material/styles';
import theme from '../../theme/theme';

describe('MainLayout Component', () => {
  test('renders children content', () => {
    render(
      <ThemeProvider theme={theme}>
        <MainLayout>
          <div>Test Child Content</div>
        </MainLayout>
      </ThemeProvider>
    );
    expect(screen.getByText('Test Child Content')).toBeInTheDocument();
  });

  test('renders a header/app bar', () => {
    render(
      <ThemeProvider theme={theme}>
        <MainLayout>
          <div>Test Child Content</div>
        </MainLayout>
      </ThemeProvider>
    );
    // Assuming the header will contain a title or a specific role
    expect(screen.getByRole('banner')).toBeInTheDocument(); 
  });

  test('renders a navigation element', () => {
    render(
      <ThemeProvider theme={theme}>
        <MainLayout>
          <div>Test Child Content</div>
        </MainLayout>
      </ThemeProvider>
    );
    // Assuming the navigation will contain a navigation role
    expect(screen.getByRole('navigation')).toBeInTheDocument();
  });
});
