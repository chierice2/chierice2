import React, { createContext, useState, useContext, useEffect, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { authService } from '../services/api';

interface User {
  id: string;
  email: string;
  name: string;
  preferred_language: string;
  created_at: string;
}

interface AuthContextData {
  user: User | null;
  token: string | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, name: string, language: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextData>({} as AuthContextData);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStorageData();
  }, []);

  async function loadStorageData() {
    try {
      const storedToken = await AsyncStorage.getItem('@LocalGuide:token');
      const storedUser = await AsyncStorage.getItem('@LocalGuide:user');

      if (storedToken && storedUser) {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
      }
    } catch (error) {
      console.error('Error loading stored data:', error);
    } finally {
      setLoading(false);
    }
  }

  async function signIn(email: string, password: string) {
    try {
      const response = await authService.login(email, password);
      setToken(response.access_token);
      setUser(response.user);

      await AsyncStorage.setItem('@LocalGuide:token', response.access_token);
      await AsyncStorage.setItem('@LocalGuide:user', JSON.stringify(response.user));
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Login failed');
    }
  }

  async function signUp(email: string, password: string, name: string, language: string) {
    try {
      const response = await authService.register(email, password, name, language);
      setToken(response.access_token);
      setUser(response.user);

      await AsyncStorage.setItem('@LocalGuide:token', response.access_token);
      await AsyncStorage.setItem('@LocalGuide:user', JSON.stringify(response.user));
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Registration failed');
    }
  }

  async function signOut() {
    setToken(null);
    setUser(null);
    await AsyncStorage.removeItem('@LocalGuide:token');
    await AsyncStorage.removeItem('@LocalGuide:user');
  }

  return (
    <AuthContext.Provider value={{ user, token, loading, signIn, signUp, signOut }}>
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}