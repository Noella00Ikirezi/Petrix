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

// Handle 401 responses with refresh token retry
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: unknown) => void;
  reject: (reason: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (token) {
      prom.resolve(token);
    } else {
      prom.reject(error);
    }
  });
  failedQueue = [];
};

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      const refreshToken = useAuthStore.getState().refreshToken;

      if (!refreshToken) {
        useAuthStore.getState().logout();
        window.location.href = '/login';
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return apiClient(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const response = await axios.post(
          `${API_BASE_URL}/api/v1/auth/refresh`,
          { refresh_token: refreshToken }
        );
        const { access_token, refresh_token } = response.data;

        useAuthStore.getState().setToken(access_token);
        useAuthStore.getState().setRefreshToken(refresh_token);

        processQueue(null, access_token);
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        useAuthStore.getState().logout();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

// Auth API (2-step MFA)
export const authApi = {
  login: async (email: string, password: string) => {
    const response = await apiClient.post('/auth/login', { email, password });
    return response.data;
  },
  verifyOtp: async (mfaToken: string, code: string) => {
    const response = await apiClient.post('/auth/verify-otp', {
      mfa_token: mfaToken,
      code,
    });
    return response.data;
  },
  refresh: async (refreshToken: string) => {
    const response = await apiClient.post('/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
  },
  logout: async () => {
    try {
      await apiClient.post('/auth/logout');
    } catch {
      // Ignore errors on logout
    }
  },
  getMe: async () => {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },
};

// Assets API
export const assetsApi = {
  list: async (params?: Record<string, unknown>) => {
    const response = await apiClient.get('/assets', { params });
    return response.data;
  },
  get: async (id: string) => {
    const response = await apiClient.get(`/assets/${id}`);
    return response.data;
  },
  create: async (data: Record<string, unknown>) => {
    const response = await apiClient.post('/assets', data);
    return response.data;
  },
  update: async (id: string, data: Record<string, unknown>) => {
    const response = await apiClient.patch(`/assets/${id}`, data);
    return response.data;
  },
  delete: async (id: string) => {
    await apiClient.delete(`/assets/${id}`);
  },
  stats: async () => {
    const response = await apiClient.get('/assets/stats/summary');
    return response.data;
  },
};

// Vulnerabilities API
export const vulnsApi = {
  list: async (params?: Record<string, unknown>) => {
    const response = await apiClient.get('/vulnerabilities', { params });
    return response.data;
  },
  get: async (id: string) => {
    const response = await apiClient.get(`/vulnerabilities/${id}`);
    return response.data;
  },
  create: async (data: Record<string, unknown>) => {
    const response = await apiClient.post('/vulnerabilities', data);
    return response.data;
  },
  update: async (id: string, data: Record<string, unknown>) => {
    const response = await apiClient.patch(`/vulnerabilities/${id}`, data);
    return response.data;
  },
  delete: async (id: string) => {
    await apiClient.delete(`/vulnerabilities/${id}`);
  },
  stats: async () => {
    const response = await apiClient.get('/vulnerabilities/stats/summary');
    return response.data;
  },
};

// Scans API
export const scansApi = {
  list: async (params?: Record<string, unknown>) => {
    const response = await apiClient.get('/scans', { params });
    return response.data;
  },
  get: async (id: string) => {
    const response = await apiClient.get(`/scans/${id}`);
    return response.data;
  },
  create: async (data: Record<string, unknown>) => {
    const response = await apiClient.post('/scans', data);
    return response.data;
  },
  start: async (id: string) => {
    const response = await apiClient.post(`/scans/${id}/start`);
    return response.data;
  },
  cancel: async (id: string) => {
    const response = await apiClient.post(`/scans/${id}/cancel`);
    return response.data;
  },
  delete: async (id: string) => {
    await apiClient.delete(`/scans/${id}`);
  },
  stats: async () => {
    const response = await apiClient.get('/scans/stats/summary');
    return response.data;
  },
};

// Pentest API
export const pentestApi = {
  // Targets
  listTargets: async (params?: Record<string, unknown>) => {
    const response = await apiClient.get('/pentest/targets', { params });
    return response.data;
  },
  getTarget: async (id: string) => {
    const response = await apiClient.get(`/pentest/targets/${id}`);
    return response.data;
  },
  createTarget: async (data: Record<string, unknown>) => {
    const response = await apiClient.post('/pentest/targets', data);
    return response.data;
  },
  updateTarget: async (id: string, data: Record<string, unknown>) => {
    const response = await apiClient.patch(`/pentest/targets/${id}`, data);
    return response.data;
  },
  deleteTarget: async (id: string) => {
    await apiClient.delete(`/pentest/targets/${id}`);
  },
  // Sessions
  listSessions: async (params?: Record<string, unknown>) => {
    const response = await apiClient.get('/pentest/sessions', { params });
    return response.data;
  },
  getSession: async (id: string) => {
    const response = await apiClient.get(`/pentest/sessions/${id}`);
    return response.data;
  },
  createSession: async (data: Record<string, unknown>) => {
    const response = await apiClient.post('/pentest/sessions', data);
    return response.data;
  },
  cancelSession: async (id: string) => {
    const response = await apiClient.post(`/pentest/sessions/${id}/cancel`);
    return response.data;
  },
  deleteSession: async (id: string) => {
    await apiClient.delete(`/pentest/sessions/${id}`);
  },
  // Findings
  getFindings: async (sessionId: string) => {
    const response = await apiClient.get(`/pentest/sessions/${sessionId}/findings`);
    return response.data;
  },
  // Attack path
  getAttackPath: async (sessionId: string) => {
    const response = await apiClient.get(`/pentest/sessions/${sessionId}/attack-path`);
    return response.data;
  },
  // AI
  enrichFindings: async (data: Record<string, unknown>) => {
    const response = await apiClient.post('/pentest/ai/enrich', data);
    return response.data;
  },
  getAiRemediation: async (findingId: string) => {
    const response = await apiClient.post(`/pentest/ai/remediation/${findingId}`);
    return response.data;
  },
  // Stats
  stats: async () => {
    const response = await apiClient.get('/pentest/stats/summary');
    return response.data;
  },
};

// Dashboard API
export const dashboardApi = {
  get: async () => {
    const response = await apiClient.get('/dashboard');
    return response.data;
  },
};

// Audit Logs API
export const auditLogsApi = {
  list: async (params?: Record<string, unknown>) => {
    const response = await apiClient.get('/audit-logs', { params });
    return response.data;
  },
};

// Export api as alias for apiClient (for components that use api directly)
export const api = apiClient;
