import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const auth = {
  login(email, password) {
    return apiClient.post('/auth/login', { email, password });
  },
  register(userData) {
    return apiClient.post('/auth/register', userData);
  },
};

export const trading = {
  getPositions() {
    return apiClient.get('/position_groups');
  },
  placeOrder(orderData) {
    return apiClient.post('/orders', orderData);
  },
};

export const risk = {
  getQueue() {
    return apiClient.get('/queue');
  },
};

export const admin = {
  getLogs() {
    return apiClient.get('/logs/system');
  },
};
