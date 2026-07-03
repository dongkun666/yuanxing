import { apiClient, requestWithRetry } from './client';
import type { User } from '../types';

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  user: User;
}

export interface RegisterResponse {
  access_token: string;
  refresh_token: string;
  user: User;
}

export const authApi = {
  login: async (email: string, password: string): Promise<LoginResponse> => {
    const response = await requestWithRetry(() =>
      apiClient.post('/api/auth/login', { email, password })
    );
    return response.data;
  },

  register: async (name: string, email: string, password: string): Promise<RegisterResponse> => {
    const response = await requestWithRetry(() =>
      apiClient.post('/api/auth/register', { name, email, password })
    );
    return response.data;
  },

  logout: async (): Promise<void> => {
    await apiClient.post('/api/auth/logout');
    localStorage.removeItem('lexprime_token');
    localStorage.removeItem('lexprime_refresh_token');
  },

  getProfile: async (): Promise<User> => {
    const response = await requestWithRetry(() =>
      apiClient.get('/api/auth/profile')
    );
    return response.data;
  },

  refreshToken: async (refreshToken: string): Promise<{ access_token: string; refresh_token: string }> => {
    const response = await apiClient.post('/api/auth/refresh', { refresh_token: refreshToken });
    return response.data;
  },
};