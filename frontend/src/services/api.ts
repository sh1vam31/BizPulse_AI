import axios from 'axios';

const rawApiUrl = import.meta.env.VITE_API_URL;
const resolvedBaseUrl = rawApiUrl
  ? rawApiUrl.startsWith('http')
    ? rawApiUrl
    : `https://${rawApiUrl.replace(/\/+$/, '')}/api/v1`
  : '/api/v1';

const api = axios.create({
  baseURL: resolvedBaseUrl,
  timeout: 300000, // 5 minutes timeout for large dataset ingestion
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to attach JWT token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('bizpulse_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor to handle auth expiry
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      if (!window.location.pathname.includes('/login')) {
        localStorage.removeItem('bizpulse_token');
        localStorage.removeItem('bizpulse_user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;

