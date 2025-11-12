import React, { useState, useEffect } from 'react';
import { ThemeProvider } from '@mui/material/styles';
import theme from './theme/theme';
import Dashboard from './components/dashboard/Dashboard';
import Positions from './components/positions/Positions';
import Login from './components/auth/Login';
import MainLayout from './components/layout/MainLayout'; // Import MainLayout
import { auth, api } from './services/api';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [positions, setPositions] = useState([]);
  const [health, setHealth] = useState(null);

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

  return (
    <ThemeProvider theme={theme}>
      <div className="App">
        {!token ? (
          <Login onLogin={handleLogin} />
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
