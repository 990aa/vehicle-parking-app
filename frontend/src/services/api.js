import axios from 'axios';

// API Configuration
const API_BASE_URL = process.env.VUE_APP_API_URL || 'http://localhost:5000/api';

// Create axios instance with defaults
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - Add auth token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - Handle errors globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle specific error cases
    if (error.response) {
      const { status, data } = error.response;
      
      // Unauthorized - clear token and redirect to login
      if (status === 401) {
        const currentPath = window.location.pathname;
        // Don't redirect if already on login/register page
        if (!currentPath.includes('/login') && !currentPath.includes('/register')) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('user_role');
          localStorage.removeItem('user');
          window.location.href = '/login';
        }
      }
      
      // Return error with message from server
      return Promise.reject({
        status,
        message: data.message || 'An error occurred',
        errors: data.errors || {},
        data
      });
    }
    
    // Network error
    if (error.code === 'ECONNABORTED') {
      return Promise.reject({
        status: 0,
        message: 'Request timed out. Please check your connection.',
        errors: { general: 'Connection timeout' }
      });
    }
    
    return Promise.reject({
      status: 0,
      message: 'Unable to connect to server. Please try again.',
      errors: { general: 'Network error' }
    });
  }
);

// Auth API
export const authAPI = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  register: (username, email, password) => api.post('/auth/register', { username, email, password }),
  getMe: () => api.get('/auth/me'),
};

// User API
export const userAPI = {
  getRole: () => api.get('/user/role'),
  getDashboardData: () => api.get('/user/dashboard-data'),
};

// Parking API
export const parkingAPI = {
  getLots: () => api.get('/parking/lots'),
  getSpots: (lotId) => api.get(`/parking/lots/${lotId}/spots`),
  reserve: (data) => api.post('/parking/reserve', data),
  cancelReservation: (id) => api.post(`/parking/reservations/${id}/cancel`),
};

// Admin API
export const adminAPI = {
  getDashboardData: () => api.get('/admin/dashboard-data'),
  getUsers: () => api.get('/admin/users'),
  getReservations: () => api.get('/admin/reservations'),
  getLots: () => api.get('/admin/lots'),
  createLot: (data) => api.post('/admin/lots', data),
};

export default api;
