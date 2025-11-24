import axios from 'axios';

// Configuration - in a real implementation, you would use environment variables
const GATEWAY_BASE_URL = process.env.REACT_APP_GATEWAY_URL || 'http://localhost:8000';

// Create service instance for the API gateway
const gatewayApi = axios.create({
  baseURL: GATEWAY_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include JWT token
gatewayApi.interceptors.request.use(
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

// Response interceptor for error handling
gatewayApi.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access - clear token and redirect
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Authentication Service API
export const authApiService = {
  login: async (email: string, password: string) => {
    try {
      const response = await gatewayApi.post('/auth/token', {
        username: email,
        password: password
      }, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      return response.data;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  },

  register: async (email: string, password: string, full_name?: string) => {
    try {
      const response = await gatewayApi.post('/auth/users', {
        email,
        password,
        full_name
      });
      return response.data;
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  },

  getProfile: async () => {
    try {
      const response = await gatewayApi.get('/auth/users/me');
      return response.data;
    } catch (error) {
      console.error('Get profile error:', error);
      throw error;
    }
  }
};

// Document Service API
export const documentApiService = {
  getDocuments: async () => {
    try {
      const response = await gatewayApi.get('/documents');
      return response.data;
    } catch (error) {
      console.error('Get documents error:', error);
      throw error;
    }
  },

  uploadDocument: async (file: File) => {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await gatewayApi.post('/documents', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      console.error('Upload document error:', error);
      throw error;
    }
  },

  getDocument: async (documentId: string) => {
    try {
      const response = await gatewayApi.get(`/documents/${documentId}`);
      return response.data;
    } catch (error) {
      console.error('Get document error:', error);
      throw error;
    }
  },

  deleteDocument: async (documentId: string) => {
    try {
      const response = await gatewayApi.delete(`/documents/${documentId}`);
      return response.data;
    } catch (error) {
      console.error('Delete document error:', error);
      throw error;
    }
  },

  getDocumentAnalysis: async (documentId: string) => {
    try {
      const response = await gatewayApi.get(`/documents/${documentId}/analysis`);
      return response.data;
    } catch (error) {
      console.error('Get document analysis error:', error);
      throw error;
    }
  },

  askQuestion: async (documentId: string, question: string) => {
    try {
      const response = await gatewayApi.post(`/documents/${documentId}/ask`, {
        question
      });
      return response.data;
    } catch (error) {
      console.error('Ask question error:', error);
      throw error;
    }
  }
};

// LLM Service API
export const llmApiService = {
  getStatus: async () => {
    try {
      const response = await gatewayApi.get('/llm/status');
      return response.data;
    } catch (error) {
      console.error('Get LLM status error:', error);
      throw error;
    }
  },

  getModels: async () => {
    try {
      const response = await gatewayApi.get('/llm/models');
      return response.data;
    } catch (error) {
      console.error('Get models error:', error);
      throw error;
    }
  },

  changeConfig: async (config: any) => {
    try {
      const response = await gatewayApi.post('/llm/config', config);
      return response.data;
    } catch (error) {
      console.error('Change config error:', error);
      throw error;
    }
  },

  testConnection: async () => {
    try {
      const response = await gatewayApi.post('/llm/test');
      return response.data;
    } catch (error) {
      console.error('Test connection error:', error);
      throw error;
    }
  }
};

// Analytics Service API
export const analyticsApiService = {
  getOverview: async (days: number = 30) => {
    try {
      const response = await gatewayApi.get(`/analytics/dashboard?days=${days}`);
      return response.data;
    } catch (error) {
      console.error('Get analytics error:', error);
      throw error;
    }
  },

  getUserStats: async () => {
    try {
      const response = await gatewayApi.get('/analytics/users');
      return response.data;
    } catch (error) {
      console.error('Get user stats error:', error);
      throw error;
    }
  },

  getDocumentStats: async () => {
    try {
      const response = await gatewayApi.get('/analytics/documents');
      return response.data;
    } catch (error) {
      console.error('Get document stats error:', error);
      throw error;
    }
  },

  getTokenStats: async () => {
    try {
      const response = await gatewayApi.get('/analytics/tokens');
      return response.data;
    } catch (error) {
      console.error('Get token stats error:', error);
      throw error;
    }
  },

  getPerformanceStats: async () => {
    try {
      const response = await gatewayApi.get('/analytics/performance');
      return response.data;
    } catch (error) {
      console.error('Get performance stats error:', error);
      throw error;
    }
  },

  getFeedbackStats: async () => {
    try {
      const response = await gatewayApi.get('/analytics/feedback');
      return response.data;
    } catch (error) {
      console.error('Get feedback stats error:', error);
      throw error;
    }
  }
};

// Storage Service API
export const storageApiService = {
  getStorageStats: async () => {
    try {
      const response = await gatewayApi.get('/storage/stats');
      return response.data;
    } catch (error) {
      console.error('Get storage stats error:', error);
      throw error;
    }
  },

  getBuckets: async () => {
    try {
      const response = await gatewayApi.get('/storage/buckets');
      return response.data;
    } catch (error) {
      console.error('Get buckets error:', error);
      throw error;
    }
  },

  cleanupStorage: async (bucket: string, retentionDays: number) => {
    try {
      const response = await gatewayApi.post('/storage/cleanup', {
        bucket,
        retentionDays
      });
      return response.data;
    } catch (error) {
      console.error('Cleanup storage error:', error);
      throw error;
    }
  }
};

// Export an aggregated service object
export default {
  auth: authApiService,
  document: documentApiService,
  llm: llmApiService,
  analytics: analyticsApiService,
  storage: storageApiService
};