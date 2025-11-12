import React from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import theme from './theme/theme';
import { AuthProvider, useAuth } from './hooks/useAuth';
import MainLayout from './components/layout/MainLayout';
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';
import DashboardPage from './pages/dashboard/DashboardPage';
import PositionsPage from './pages/positions/PositionsPage';
import PerformancePage from './pages/dashboard/PerformancePage';
import SystemLogsPage from './pages/admin/SystemLogsPage';
import SettingsPage from './pages/admin/SettingsPage';
import NotFoundPage from './pages/NotFoundPage';

const PrivateRoute = ({ children }) => {
  const { token } = useAuth();
  return token ? <MainLayout>{children}</MainLayout> : <Navigate to="/login" />;
};

const App = () => {
  return (
    <ThemeProvider theme={theme}>
      <AuthProvider>
        <Router>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/" element={<PrivateRoute><DashboardPage /></PrivateRoute>} />
            <Route path="/positions" element={<PrivateRoute><PositionsPage /></PrivateRoute>} />
            <Route path="/performance" element={<PrivateRoute><PerformancePage /></PrivateRoute>} />
            <Route path="/logs" element={<PrivateRoute><SystemLogsPage /></PrivateRoute>} />
            <Route path="/settings" element={<PrivateRoute><SettingsPage /></PrivateRoute>} />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;