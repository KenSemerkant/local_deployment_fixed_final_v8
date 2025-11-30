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
  error_message?: string;
  processing_step?: string;
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

  // Download document
  downloadDocument: async (documentId: string, filename: string): Promise<void> => {
    console.log(`Downloading document ${documentId}`);
    try {
      // Direct download via browser navigation
      // This allows the browser to handle the Content-Disposition header and filename correctly
      const token = localStorage.getItem('token');
      // Append token just in case, though currently not enforced for download
      const downloadUrl = `${API_URL}/documents/${documentId}/download?token=${token}`;

      // Create a temporary link to trigger download without replacing current page
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.setAttribute('download', filename); // Hint to browser, but server header takes precedence
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      console.log(`Triggered download for document ${documentId}`);
    } catch (error) {
      console.error(`Error downloading document ${documentId}:`, error);
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

  // Upload document from URL
  uploadFromUrl: async (url: string): Promise<Document> => {
    console.log(`Uploading document from URL: ${url}`);
    try {
      const response = await api.post('/documents/upload-url', { url });
      console.log('Upload from URL response:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error uploading document from URL:', error);
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

  // Cancel document processing
  cancelProcessing: async (documentId: string): Promise<{ message: string }> => {
    console.log(`Cancelling processing for document ${documentId}`);
    try {
      const response = await api.post(`/documents/${documentId}/cancel`);
      console.log(`Document ${documentId} processing cancelled:`, response.data);
      return response.data;
    } catch (error) {
      console.error(`Error cancelling processing for document ${documentId}:`, error);
      throw error;
    }
  },

  // Get document processing status
  getProcessingStatus: async (documentId: string): Promise<{
    document_id: number;
    status: string;
    is_processing: boolean;
    can_cancel: boolean;
  }> => {
    console.log(`Getting processing status for document ${documentId}`);
    try {
      const response = await api.get(`/documents/${documentId}/status`);
      console.log(`Document ${documentId} processing status:`, response.data);
      return response.data;
    } catch (error) {
      console.error(`Error getting processing status for document ${documentId}:`, error);
      throw error;
    }
  },
};

export const authService = {
  // Update user profile
  updateProfile: async (data: { full_name?: string; email?: string; avatar_url?: string; password?: string }): Promise<any> => {
    console.log('Updating user profile:', data);
    try {
      const response = await api.put('/users/me', data);
      console.log('Update profile response:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error updating profile:', error);
      throw error;
    }
  }
};

export const storageService = {
  // Upload avatar
  uploadAvatar: async (file: File): Promise<{ filename: string; url: string }> => {
    console.log(`Uploading avatar: ${file.name}`);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await api.post('/storage/avatars/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      console.log('Avatar upload response:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error uploading avatar:', error);
      throw error;
    }
  }
};

export default api;
