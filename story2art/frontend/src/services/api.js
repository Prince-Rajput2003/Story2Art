import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const normalizeApiError = (error, fallbackMessage = 'Something went wrong. Please try again.') => {
  if (!error) return fallbackMessage;

  const data = error?.response?.data;

  if (typeof data?.detail === 'string') return data.detail;
  if (Array.isArray(data?.detail)) {
    return data.detail
      .map((item) => item?.msg || item?.message || 'Invalid field')
      .filter(Boolean)
      .join(', ');
  }
  if (data?.detail && typeof data?.detail === 'object') {
    const detail = data.detail;
    if (detail.msg) return detail.msg;
    if (detail.message) return detail.message;
    if (detail.error) return detail.error;
    return JSON.stringify(detail);
  }
  if (typeof data?.message === 'string') return data.message;
  if (typeof error?.message === 'string') {
    if (error.message.includes('Network Error')) {
      return 'Backend is temporarily unavailable. Please try again in a moment.';
    }
    return error.message;
  }

  return fallbackMessage;
};

export const setAuthToken = (token) => {
  if (token) {
    api.defaults.headers.common.Authorization = `Bearer ${token}`;
    localStorage.setItem('story2art_token', token);
  } else {
    delete api.defaults.headers.common.Authorization;
    localStorage.removeItem('story2art_token');
  }
};

const savedToken = localStorage.getItem('story2art_token');
if (savedToken) {
  setAuthToken(savedToken);
}

export const fetchHealth = () => api.get('/api/health');
export const enhanceStory = (story) => api.post('/api/enhance-story', { story });
export const generateStoryImage = (payload) => api.post('/api/generate', payload);
export const getGallery = () => api.get('/api/gallery');
export const deleteImage = (imageId) => api.delete(`/api/gallery/${imageId}`);

export const registerUser = (payload) => api.post('/api/auth/register', payload);
export const loginUser = (payload) => api.post('/api/auth/login', payload);
export const getCurrentUser = () => api.get('/api/auth/me');
export const updateProfile = (payload) => api.put('/api/auth/profile', payload);
export const logoutUser = () => api.post('/api/auth/logout');
export const requestPasswordReset = (payload) => api.post('/api/auth/forgot-password', payload);
export const resetPassword = (payload) => api.post('/api/auth/reset-password', payload);

export const getPlans = () => api.get('/api/plans');
export const startCheckout = (payload) => api.post('/api/subscriptions/checkout', payload);
export const verifyPayment = (payload) => api.post('/api/payments/verify', payload);
export const getPaymentHistory = () => api.get('/api/payments/history');

export const getAdminDashboard = () => api.get('/api/admin/dashboard');
export const getAdminUsers = () => api.get('/api/admin/users');
export const toggleUserStatus = (userId) => api.post(`/api/admin/users/${userId}/toggle-status`);
export const changeUserRole = (userId, role) => api.post(`/api/admin/users/${userId}/role`, { role });
export const adjustCredits = (userId, amount) => api.post(`/api/admin/users/${userId}/credits`, { amount });

export default api;
