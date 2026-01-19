import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Tasks API
export const tasksAPI = {
  getAll: (params?: any) => apiClient.get('/api/tasks', { params }),
  getById: (id: number) => apiClient.get(`/api/tasks/${id}`),
  create: (data: any) => apiClient.post('/api/tasks', data),
  update: (id: number, data: any) => apiClient.patch(`/api/tasks/${id}`, data),
  delete: (id: number) => apiClient.delete(`/api/tasks/${id}`),
};

// Projects API
export const projectsAPI = {
  getAll: () => apiClient.get('/api/projects'),
  getById: (id: number) => apiClient.get(`/api/projects/${id}`),
  create: (data: any) => apiClient.post('/api/projects', data),
  update: (id: number, data: any) => apiClient.patch(`/api/projects/${id}`, data),
  delete: (id: number) => apiClient.delete(`/api/projects/${id}`),
};

// Calendar API
export const calendarAPI = {
  getEvents: (params?: any) => apiClient.get('/api/calendar', { params }),
  createEvent: (data: any) => apiClient.post('/api/calendar', data),
  updateEvent: (id: number, data: any) => apiClient.patch(`/api/calendar/${id}`, data),
  deleteEvent: (id: number) => apiClient.delete(`/api/calendar/${id}`),
};

// AI API
export const aiAPI = {
  prioritize: (data: any) => apiClient.post('/api/ai/prioritize', data),
  generateEmail: (data: any) => apiClient.post('/api/ai/generate-email', data),
  generateDocument: (data: any) => apiClient.post('/api/ai/generate-document', data),
  chat: (data: any) => apiClient.post('/api/ai/chat', data),
};

// Documents API
export const documentsAPI = {
  getAll: (params?: any) => apiClient.get('/api/documents', { params }),
  getById: (id: number) => apiClient.get(`/api/documents/${id}`),
  create: (data: any) => apiClient.post('/api/documents', data),
  update: (id: number, data: any) => apiClient.patch(`/api/documents/${id}`, data),
  delete: (id: number) => apiClient.delete(`/api/documents/${id}`),
};

// Knowledge API
export const knowledgeAPI = {
  getAll: (params?: any) => apiClient.get('/api/knowledge', { params }),
  getById: (id: number) => apiClient.get(`/api/knowledge/${id}`),
  create: (data: any) => apiClient.post('/api/knowledge', data),
  update: (id: number, data: any) => apiClient.patch(`/api/knowledge/${id}`, data),
  delete: (id: number) => apiClient.delete(`/api/knowledge/${id}`),
};
