import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export const auth = {
  login(email, password) {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    return apiClient.post('/auth/token', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
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

export const config = {
  getConfig() {
    return apiClient.get('/config');
  },
  updateConfig(configData) {
    return apiClient.put('/config', configData);
  },
};

export const analytics = {
  getAnalytics() {
    return apiClient.get('/analytics');
  },
};

export const api = {
  get: (url) => apiClient.get(url),
  post: (url, data) => apiClient.post(url, data),
  put: (url, data) => apiClient.put(url, data),
};
