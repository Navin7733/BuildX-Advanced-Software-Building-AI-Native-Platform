import axios from 'axios';
import useStore from '../store/useStore';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add JWT token
api.interceptors.request.use((config) => {
  const token = useStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor to handle token refresh (simplified for MVP)
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = useStore.getState().refreshToken;
      
      if (refreshToken) {
        try {
          const res = await axios.post(`${API_URL}/auth/refresh/`, { refresh: refreshToken });
          useStore.getState().setTokens(res.data.access, refreshToken);
          api.defaults.headers.common['Authorization'] = `Bearer ${res.data.access}`;
          return api(originalRequest);
        } catch (err) {
          useStore.getState().logout();
        }
      } else {
        useStore.getState().logout();
      }
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  login: (email, password) => api.post('/auth/login/', { email, password }),
  register: (name, email, password) => api.post('/auth/register/', { name, email, password }),
  me: () => api.get('/auth/me/'),
};

export const projectApi = {
  list: () => api.get('/projects/'),
  create: (data) => api.post('/projects/', data),
  get: (id) => api.get(`/projects/${id}/`),
  getFiles: (id) => api.get(`/projects/${id}/files/`),
  getFileContent: (id, path) => api.get(`/projects/${id}/files/${encodeURIComponent(path)}/`),
  getDecisions: (id) => api.get(`/projects/${id}/decisions/`),
};

export const agentApi = {
  runWorkflow: (projectId, input) => api.post(`/projects/${projectId}/agents/run/`, { input }),
  runAgent: (projectId, agentType, input) => api.post(`/projects/${projectId}/agents/${agentType}/run/`, { input }),
  listRuns: (projectId) => api.get(`/projects/${projectId}/agents/runs/`),
};

export const memoryApi = {
  list: (projectId) => api.get(`/projects/${projectId}/memory/`),
  search: (projectId, query) => api.post(`/projects/${projectId}/memory/search/`, { query }),
};

export default api;
