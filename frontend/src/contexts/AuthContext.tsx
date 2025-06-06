import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import axios from 'axios';

// API base URL from environment variable
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface User {
  id: number;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
  updated_at: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, full_name?: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    // Set up axios defaults
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      console.log('Token set in axios defaults:', token);
    } else {
      delete axios.defaults.headers.common['Authorization'];
      console.log('Token removed from axios defaults');
    }
  }, [token]);

  useEffect(() => {
    const fetchUser = async () => {
      if (!token) {
        setIsLoading(false);
        console.log('No token found, skipping user fetch');
        return;
      }

      try {
        console.log('Fetching user data from:', `${API_URL}/users/me`);
        const response = await axios.get(`${API_URL}/users/me`);
        console.log('User data received:', response.data);
        setUser(response.data);
      } catch (error: any) {
        console.error('Error fetching user:', error);
        console.error('Error response:', error.response?.data);
        // If token is invalid, clear it
        localStorage.removeItem('token');
        setToken(null);
      } finally {
        setIsLoading(false);
      }
    };

    fetchUser();
  }, [token]);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      console.log('Attempting login with:', { email });
      // Use URLSearchParams for form data - FIXED: using correct /token endpoint
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      console.log('Sending login request to:', `${API_URL}/token`);
      const response = await axios.post(`${API_URL}/token`, formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      console.log('Login response:', response.data);
      const { access_token } = response.data;
      localStorage.setItem('token', access_token);
      setToken(access_token);
    } catch (error: any) {
      console.error('Login error:', error);
      console.error('Error response:', error.response?.data);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (email: string, password: string, full_name?: string) => {
    setIsLoading(true);
    try {
      console.log('Attempting registration with:', { email, full_name });
      const response = await axios.post(`${API_URL}/users/`, {
        email,
        password,
        full_name,
      });

      console.log('Registration response:', response.data);
      // After registration, login automatically
      await login(email, password);
    } catch (error: any) {
      console.error('Registration error:', error);
      console.error('Error response:', error.response?.data);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    console.log('Logging out, removing token');
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  const value = {
    user,
    token,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
