import axios from 'axios';

// API base URL from environment variable
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      console.log(`API Request to ${config.url} with auth token`);
      config.headers.Authorization = `Bearer ${token}`;
    } else {
      console.log(`API Request to ${config.url} without auth token`);
    }
    return config;
  },
  (error) => {
    console.error('API Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for debugging
api.interceptors.response.use(
  (response) => {
    console.log(`API Response from ${response.config.url}:`, response.status);
    return response;
  },
  (error) => {
    console.error(`API Error from ${error.config?.url}:`, error.response?.status, error.response?.data);
    return Promise.reject(error);
  }
);

// Document types
export interface Document {
  id: number;
  filename: string;
  mime_type: string;
  file_size: number;
  status: string;
  created_at: string;
  updated_at: string;
  owner_id?: number;
  analysis_results?: AnalysisResults;
}

export interface AnalysisResults {
  summary?: string;
  key_figures?: string; // JSON string that needs to be parsed
  vector_db_path?: string;
  error?: string;
}

export interface KeyFigure {
  name: string;
  value: string;
  source_page?: number;
  source_section?: string;
}

export interface SourceReference {
  page?: number;
  snippet?: string;
  section?: string;
}

export interface QuestionResponse {
  id: number;
  question_text: string;
  answer_text: string;
  sources: SourceReference[];
  created_at: string;
}

// API functions
export const documentService = {
  // Get all documents for current user
  getDocuments: async (): Promise<Document[]> => {
    console.log('Fetching documents from /documents/');
    try {
      const response = await api.get('/documents/');
      console.log('Documents response data:', response.data);
      // Return the direct array from the backend
      return response.data;
    } catch (error) {
      console.error('Error fetching documents:', error);
      throw error;
    }
  },

  // Get document by ID
  getDocument: async (documentId: string): Promise<Document> => {
    console.log(`Fetching document ${documentId}`);
    try {
      const response = await api.get(`/documents/${documentId}`);
      console.log('Document response data:', response.data);

      // If document is completed, also fetch analysis results
      const document = response.data;
      if (document.status === 'COMPLETED') {
        try {
          const analysisResponse = await api.get(`/documents/${documentId}/analysis`);
          console.log('Analysis response data:', analysisResponse.data);

          // Combine document and analysis data
          document.analysis_results = {
            summary: analysisResponse.data.summary,
            key_figures: JSON.stringify(analysisResponse.data.key_figures),
            vector_db_path: analysisResponse.data.vector_db_path
          };
        } catch (analysisError) {
          console.warn(`Could not fetch analysis for document ${documentId}:`, analysisError);
          // Don't throw error here, just continue without analysis results
        }
      }

      return document;
    } catch (error) {
      console.error(`Error fetching document ${documentId}:`, error);
      throw error;
    }
  },

  // Upload document
  uploadDocument: async (file: File): Promise<Document> => {
    console.log(`Uploading document: ${file.name}`);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await api.post('/documents', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      console.log('Upload response:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error uploading document:', error);
      throw error;
    }
  },

  // Delete document
  deleteDocument: async (documentId: string): Promise<void> => {
    console.log(`Deleting document ${documentId}`);
    try {
      await api.delete(`/documents/${documentId}`);
      console.log(`Document ${documentId} deleted successfully`);
    } catch (error) {
      console.error(`Error deleting document ${documentId}:`, error);
      throw error;
    }
  },

  // Ask question about document
  askQuestion: async (documentId: string, question: string): Promise<QuestionResponse> => {
    console.log(`Asking question about document ${documentId}: "${question}"`);
    try {
      const response = await api.post(`/documents/${documentId}/ask`, { question });
      console.log('Question response:', response.data);
      return response.data;
    } catch (error) {
      console.error(`Error asking question about document ${documentId}:`, error);
      throw error;
    }
  },

  // Get conversation history for document
  getConversationHistory: async (documentId: string): Promise<QuestionResponse[]> => {
    console.log(`Fetching conversation history for document ${documentId}`);
    try {
      const response = await api.get(`/documents/${documentId}/questions`);
      console.log('Conversation history response:', response.data);
      return response.data;
    } catch (error) {
      console.error(`Error fetching conversation history for document ${documentId}:`, error);
      throw error;
    }
  },

  // Export document analysis
  exportDocument: async (documentId: string, format: 'txt' | 'csv' = 'csv'): Promise<{ export_url: string; expires_at: string }> => {
    console.log(`Exporting document ${documentId} as ${format}`);
    try {
      const response = await api.post(`/documents/${documentId}/export`, { format });
      console.log('Export response:', response.data);
      return response.data;
    } catch (error) {
      console.error(`Error exporting document ${documentId}:`, error);
      throw error;
    }
  },

  // Update document status (for client-side uploads)
  updateStatus: async (documentId: string, status: string): Promise<void> => {
    console.log(`Updating status of document ${documentId} to ${status}`);
    try {
      await api.patch(`/documents/${documentId}/status`, { status });
      console.log(`Document ${documentId} status updated to ${status}`);
    } catch (error) {
      console.error(`Error updating status of document ${documentId}:`, error);
      throw error;
    }
  },
};

export default api;
