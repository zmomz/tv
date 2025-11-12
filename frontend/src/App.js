import React, { useState, useEffect } from 'react';
import { ThemeProvider } from '@mui/material/styles';
import theme from './theme/theme';
import Dashboard from './components/dashboard/Dashboard';
import Positions from './components/positions/Positions';
import Login from './components/auth/Login';
import Register from './components/auth/Register'; // Import the new Register component
import MainLayout from './components/layout/MainLayout';
import { auth, api } from './services/api';
import { Box, Link } from '@mui/material';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [positions, setPositions] = useState([]);
  const [health, setHealth] = useState(null);
  const [showRegister, setShowRegister] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      if (token) {
        try {
          const [positionsResponse, healthResponse] = await Promise.all([
            api.get('/positions'),
            api.get('/health'),
          ]);
          setPositions(positionsResponse.data);
          setHealth(healthResponse.data);
        } catch (error) {
          console.error(error);
        }
      }
    };

    fetchData();
  }, [token]);

  const handleLogin = async (email, password) => {
    try {
      const response = await auth.login(email, password);
      localStorage.setItem('token', response.data.access_token);
      setToken(response.data.access_token);
    } catch (error) {
      console.error(error);
    }
  };

  const handleRegister = async (username, email, password) => {
    try {
      await auth.register(username, email, password);
      // After successful registration, automatically log in the user
      await handleLogin(email, password);
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <div className="App">
        {!token ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mt: 8 }}>
            {showRegister ? (
              <Register onRegister={handleRegister} />
            ) : (
              <Login onLogin={handleLogin} />
            )}
            <Link component="button" variant="body2" onClick={() => setShowRegister(!showRegister)} sx={{ mt: 2 }}>
              {showRegister ? 'Already have an account? Sign In' : 'Don't have an account? Sign Up'}
            </Link>
          </Box>
        ) : (
          <MainLayout>
            <Dashboard health={health} />
            <Positions positions={positions} />
          </MainLayout>
        )}
      </div>
    </ThemeProvider>
  );
}

export default App;
