import axios from 'axios';

// API base URL from environment variable - now pointing to the gateway
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token'); // Assuming JWT token storage
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for debugging
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export default api;

// API services
export const authService = {
  login: async (email: string, password: string) => {
    const response = await api.post('/api/auth/token', {
      username: email,
      password: password
    });
    return response.data;
  },

  register: async (email: string, password: string, full_name?: string) => {
    const response = await api.post('/api/auth/users', {
      email,
      password,
      full_name
    });
    return response.data;
  },

  getProfile: async () => {
    const response = await api.get('/api/auth/users/me');
    return response.data;
  }
};

export const documentService = {
  getDocuments: async () => {
    const response = await api.get('/api/documents');
    return response.data;
  },

  uploadDocument: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/api/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  getDocument: async (documentId: string) => {
    const response = await api.get(`/api/documents/${documentId}`);
    return response.data;
  },

  deleteDocument: async (documentId: string) => {
    const response = await api.delete(`/api/documents/${documentId}`);
    return response.data;
  },

  getDocumentAnalysis: async (documentId: string) => {
    const response = await api.get(`/api/documents/${documentId}/analysis`);
    return response.data;
  },

  askQuestion: async (documentId: string, question: string) => {
    const response = await api.post(`/api/documents/${documentId}/ask`, {
      question
    });
    return response.data;
  }
};

export const llmService = {
  getStatus: async () => {
    const response = await api.get('/api/llm/status');
    return response.data;
  },

  getModels: async () => {
    const response = await api.get('/api/llm/models');
    return response.data;
  },

  getVendors: async () => {
    const response = await api.get('/api/llm/vendors');
    return response.data;
  },

  changeMode: async (mode: string, model?: string, apiKey?: string) => {
    const response = await api.post('/api/llm/mode', {
      mode,
      model,
      apiKey
    });
    return response.data;
  }
};

export const analyticsService = {
  getOverview: async (days: number = 30) => {
    const response = await api.get(`/api/analytics/overview?days=${days}`);
    return response.data;
  },

  getUsagePatterns: async (days: number = 30) => {
    const response = await api.get(`/api/analytics/usage-patterns?days=${days}`);
    return response.data;
  },

  getTokenAnalytics: async (days: number = 30) => {
    const response = await api.get(`/api/analytics/tokens?days=${days}`);
    return response.data;
  },

  getPerformanceAnalytics: async (days: number = 30) => {
    const response = await api.get(`/api/analytics/performance?days=${days}`);
    return response.data;
  },

  getUserSatisfaction: async (days: number = 30) => {
    const response = await api.get(`/api/analytics/satisfaction?days=${days}`);
    return response.data;
  }
};

export const storageService = {
  getStorageOverview: async () => {
    const response = await api.get('/api/storage/overview');
    return response.data;
  },

  getUserStorage: async (userId?: number) => {
    const url = userId ? `/api/storage/users/${userId}` : '/api/storage/users';
    const response = await api.get(url);
    return response.data;
  },

  cleanupOrphanedFiles: async () => {
    const response = await api.post('/api/storage/cleanup/orphaned');
    return response.data;
  },

  cleanupUserStorage: async (userId: number) => {
    const response = await api.post(`/api/storage/cleanup/user/${userId}`);
    return response.data;
  }
};