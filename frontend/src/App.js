import React, { useState, useEffect } from 'react';
import Dashboard from './components/dashboard/Dashboard';
import Positions from './components/positions/Positions';
import { auth, api } from './services/api';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
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

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await auth.login(email, password);
      localStorage.setItem('token', response.data.access_token);
      setToken(response.data.access_token);
    } catch (error) {
      console.error(error);
    }
  };

  if (!token) {
    return (
      <div className="App">
        <h1>Login</h1>
        <form onSubmit={handleLogin}>
          <label>
            Email:
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </label>
          <label>
            Password:
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
          <button type="submit">Login</button>
        </form>
      </div>
    );
  }

  return (
    <div className="App">
      <Dashboard health={health} />
      <Positions positions={positions} />
    </div>
  );
}

export default App;
