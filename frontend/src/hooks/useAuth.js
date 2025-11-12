import React, { createContext, useState, useContext, useEffect } from 'react';
import { auth } from '../services/api';
import jwtDecode from 'jwt-decode';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [user, setUser] = useState(null);

  useEffect(() => {
    if (token) {
      try {
        const decoded = jwtDecode(token);
        setUser(decoded);
      } catch (error) {
        console.error("Invalid token", error);
        logout();
      }
    }
  }, [token]);

  const login = async (email, password) => {
    const response = await auth.login(email, password);
    const { access_token } = response.data;
    localStorage.setItem('token', access_token);
    setToken(access_token);
    const decoded = jwtDecode(access_token);
    setUser(decoded);
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  const register = async (username, email, password) => {
    await auth.register({ username, email, password, role: 'trader' });
    await login(email, password);
  };

  return (
    <AuthContext.Provider value={{ token, user, login, logout, register }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
