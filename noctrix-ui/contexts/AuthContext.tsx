"use client";

import React, { createContext, useState, useContext, useEffect, ReactNode } from 'react';
import apiClient from '@/lib/api';

interface User {
  username: string;
  role: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<any>;
  logout: () => void;
}
const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  useEffect(() => {
    const checkUserStatus = async () => {
      try {
        const response = await apiClient.get('/users/me'); 
        if (response.data) {
          setUser({ username: response.data.usr, role: response.data.role });
        }
      } catch (error) {
        console.log("No active session found.");
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };
    checkUserStatus();
  }, []);
  
    const login = async (username: string, password: string): Promise<any> => {
    const response = await apiClient.post('/auth/login', { username, password });
    if (response.data && response.data.ok) {
        setUser({ username: username, role: response.data.role });
    }
    return response.data;
  };

  const logout = async () => {
    try {
      await apiClient.post('/auth/logout');
    } catch (error) {
      console.error("Logout failed, clearing session locally.", error);
    } finally {
      setUser(null);
      window.location.href = '/login';
    }
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};