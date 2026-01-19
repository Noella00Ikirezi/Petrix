import axios from 'axios';
import { useAuthStore } from '@/stores/authStore';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 responses
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  login: async (email: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const response = await apiClient.post('/auth/login/', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return response.data;
  },
  getMe: async () => {
    const response = await apiClient.get('/auth/me/');
    return response.data;
  },
};

// Assets API
export const assetsApi = {
  list: async (params?: Record<string, unknown>) => {
    const response = await apiClient.get('/assets/', { params });
    return response.data;
  },
  get: async (id: string) => {
    const response = await apiClient.get(`/assets/${id}/`);
    return response.data;
  },
  create: async (data: Record<string, unknown>) => {
    const response = await apiClient.post('/assets/', data);
    return response.data;
  },
  update: async (id: string, data: Record<string, unknown>) => {
    const response = await apiClient.patch(`/assets/${id}/`, data);
    return response.data;
  },
  delete: async (id: string) => {
    await apiClient.delete(`/assets/${id}/`);
  },
  stats: async () => {
    const response = await apiClient.get('/assets/stats/summary/');
    return response.data;
  },
};

// Vulnerabilities API
export const vulnsApi = {
  list: async (params?: Record<string, unknown>) => {
    const response = await apiClient.get('/vulnerabilities/', { params });
    return response.data;
  },
  get: async (id: string) => {
    const response = await apiClient.get(`/vulnerabilities/${id}/`);
    return response.data;
  },
  create: async (data: Record<string, unknown>) => {
    const response = await apiClient.post('/vulnerabilities/', data);
    return response.data;
  },
  update: async (id: string, data: Record<string, unknown>) => {
    const response = await apiClient.patch(`/vulnerabilities/${id}/`, data);
    return response.data;
  },
  delete: async (id: string) => {
    await apiClient.delete(`/vulnerabilities/${id}/`);
  },
  stats: async () => {
    const response = await apiClient.get('/vulnerabilities/stats/summary/');
    return response.data;
  },
};

// Scans API
export const scansApi = {
  list: async (params?: Record<string, unknown>) => {
    const response = await apiClient.get('/scans/', { params });
    return response.data;
  },
  get: async (id: string) => {
    const response = await apiClient.get(`/scans/${id}/`);
    return response.data;
  },
  create: async (data: Record<string, unknown>) => {
    const response = await apiClient.post('/scans/', data);
    return response.data;
  },
  start: async (id: string) => {
    const response = await apiClient.post(`/scans/${id}/start/`);
    return response.data;
  },
  cancel: async (id: string) => {
    const response = await apiClient.post(`/scans/${id}/cancel/`);
    return response.data;
  },
  delete: async (id: string) => {
    await apiClient.delete(`/scans/${id}/`);
  },
  stats: async () => {
    const response = await apiClient.get('/scans/stats/summary/');
    return response.data;
  },
};

// Dashboard API
export const dashboardApi = {
  get: async () => {
    const response = await apiClient.get('/dashboard/');
    return response.data;
  },
};
