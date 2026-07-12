/**
 * Couche d'accès HTTP de Petrix.
 * Configure une instance Axios partagée avec injection automatique du token JWT,
 * gestion transparente du refresh token (file d'attente anti-concurrence),
 * et expose un objet API par domaine fonctionnel (auth, assets, vulns, scans…).
 */
import axios from 'axios';
import { useAuthStore } from '@/stores/authStore';

// En prod (via nginx) : URL relative '' → nginx proxie /api/ vers le backend
// En dev local : VITE_API_URL=http://localhost:8000 dans .env
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Intercepteur de requête : injecte le Bearer token JWT dans l'en-tête Authorization
 * si l'utilisateur est actuellement authentifié.
 */
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

/**
 * Résout ou rejette toutes les requêtes en attente après une tentative de refresh.
 * @param error - Erreur à propager si le refresh a échoué (null si succès).
 * @param token - Nouveau access token à injecter si le refresh a réussi.
 */
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

/**
 * API d'authentification : inscription, connexion en deux étapes (MFA email OTP),
 * rafraîchissement de token et récupération du profil courant.
 */
// Auth API (2-step MFA)
export const authApi = {
  signup: async (email?: string, password?: string, firstName?: string, lastName?: string) => {
    const response = await apiClient.post('/auth/register', {
      email,
      password,
      first_name: firstName,
      last_name: lastName,
    });
    return response.data;
  },
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

/** CRUD complet sur les actifs (assets) de l'inventaire ; inclut un endpoint de statistiques globales. */
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

/** CRUD sur les vulnérabilités CVE enregistrées dans la base Petrix ; inclut un résumé statistique. */
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

/** Gestion du cycle de vie des scans : création, démarrage, annulation et consultation des findings. */
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
  findings: async (id: string) => {
    const response = await apiClient.get(`/scans/${id}/findings`);
    return response.data;
  },
  assets: async (id: string) => {
    const response = await apiClient.get(`/scans/${id}/assets`);
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

/**
 * API de durcissement (HCO) ANSSI-BP-028 : modules, cibles, sessions d'audit,
 * findings, rapport complet, import XML agent et chat IA (Mistral).
 */
// Hardening (HCO) API
export const hardeningApi = {
  listModules: async () => {
    const response = await apiClient.get('/hardening/modules');
    return response.data;
  },
  // Targets
  listTargets: async () => {
    const response = await apiClient.get('/hardening/targets');
    return response.data;
  },
  createTarget: async (data: Record<string, unknown>) => {
    const response = await apiClient.post('/hardening/targets', data);
    return response.data;
  },
  deleteTarget: async (id: string) => {
    await apiClient.delete(`/hardening/targets/${id}`);
  },
  // Sessions
  listSessions: async () => {
    const response = await apiClient.get('/hardening/sessions');
    return response.data;
  },
  getSession: async (id: string) => {
    const response = await apiClient.get(`/hardening/sessions/${id}`);
    return response.data;
  },
  createSession: async (data: Record<string, unknown>) => {
    const response = await apiClient.post('/hardening/sessions', data);
    return response.data;
  },
  getFindings: async (sessionId: string) => {
    const response = await apiClient.get(`/hardening/sessions/${sessionId}/findings`);
    return response.data;
  },
  getFullReport: async (sessionId: string) => {
    const response = await apiClient.get(`/hardening/sessions/${sessionId}/report`);
    return response.data;
  },
  importXml: async (file: File) => {
    const form = new FormData();
    form.append('file', file);
    const response = await apiClient.post('/hardening/import-xml', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  aiChat: async (sessionId: string, question: string): Promise<{ answer: string }> => {
    const response = await apiClient.post(`/hardening/sessions/${sessionId}/ai-chat`, { question });
    return response.data;
  },
};

/** Flux CERT-FR (alertes, avis, IOC…) et corrélations CVE avec les vulnérabilités locales. */
export const feedApi = {
  certFr: async (feedType: 'alerte' | 'avis' | 'dur' | 'ioc' | 'actualite' = 'alerte') => {
    const response = await apiClient.get(`/feed/cert-fr?feed_type=${feedType}`);
    return response.data;
  },
  certFrMulti: async () => {
    const response = await apiClient.get('/feed/cert-fr/multi');
    return response.data;
  },
  certFrFiche: async (certId: string, feedType = 'alerte') => {
    const response = await apiClient.get(`/feed/cert-fr/fiche?cert_id=${certId}&feed_type=${feedType}`);
    return response.data;
  },
  vulnCorrelations: async () => {
    const response = await apiClient.get('/feed/vuln-correlations');
    return response.data;
  },
};

/** Corrélations entre les findings d'une session de durcissement et les alertes CERT-FR. */
export const hardeningCorrelationsApi = {
  sessionCorrelations: async (sessionId: string) => {
    const response = await apiClient.get(`/hardening/sessions/${sessionId}/cert-correlations`);
    return response.data;
  },
};

// Export api as alias for apiClient (for components that use api directly)
export const api = apiClient;
