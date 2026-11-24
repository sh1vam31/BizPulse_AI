import React, { createContext, useContext, useEffect, useState } from 'react';
import api from '../services/api';

export interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  organization_id: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string, organizationName: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('bizpulse_token'));
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchMe = async () => {
      const storedToken = localStorage.getItem('bizpulse_token');
      if (storedToken) {
        try {
          const res = await api.get('/auth/me');
          setUser(res.data);
        } catch (e) {
          localStorage.removeItem('bizpulse_token');
          localStorage.removeItem('bizpulse_user');
          setToken(null);
          setUser(null);
        }
      }
      setIsLoading(false);
    };
    fetchMe();
  }, []);

  const login = async (email: string, password: string) => {
    const res = await api.post('/auth/login', { email, password });
    const { access_token, user: userData } = res.data;
    localStorage.setItem('bizpulse_token', access_token);
    localStorage.setItem('bizpulse_user', JSON.stringify(userData));
    setToken(access_token);
    setUser(userData);
  };

  const register = async (name: string, email: string, password: string, organizationName: string) => {
    const res = await api.post('/auth/register', {
      name,
      email,
      password,
      organization_name: organizationName,
      role: 'Business Owner',
    });
    const { access_token, user: userData } = res.data;
    localStorage.setItem('bizpulse_token', access_token);
    localStorage.setItem('bizpulse_user', JSON.stringify(userData));
    setToken(access_token);
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem('bizpulse_token');
    localStorage.removeItem('bizpulse_user');
    setToken(null);
    setUser(null);
    window.location.href = '/login';
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token && !!user,
        isLoading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

