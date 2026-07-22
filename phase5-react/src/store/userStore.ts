import { create } from 'zustand';
import type { User } from '../types';

interface UserStore {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  currentPage: string;
  
  login: (user: User, token: string, refreshToken: string) => void;
  logout: () => void;
  setUser: (user: User | null) => void;
  setCurrentPage: (page: string) => void;
  loadFromStorage: () => void;
}

export const useUserStore = create<UserStore>((set) => ({
  user: null,
  token: null,
  refreshToken: null,
  isAuthenticated: false,
  currentPage: '/workstation',

  login: (user, token, refreshToken) => {
    localStorage.setItem('lexprime_token', token);
    localStorage.setItem('lexprime_refresh_token', refreshToken);
    localStorage.setItem('lexprime_user', JSON.stringify(user));
    set({
      user,
      token,
      refreshToken,
      isAuthenticated: true,
    });
  },

  logout: () => {
    localStorage.removeItem('lexprime_token');
    localStorage.removeItem('lexprime_refresh_token');
    localStorage.removeItem('lexprime_user');
    set({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      currentPage: '/login',
    });
  },

  setUser: (user) => {
    if (user) {
      localStorage.setItem('lexprime_user', JSON.stringify(user));
    } else {
      localStorage.removeItem('lexprime_user');
    }
    set({ user });
  },

  setCurrentPage: (page) => set({ currentPage: page }),

  loadFromStorage: () => {
    const token = localStorage.getItem('lexprime_token');
    const refreshToken = localStorage.getItem('lexprime_refresh_token');
    const userStr = localStorage.getItem('lexprime_user');
    
    if (token && refreshToken) {
      let user: User | null = null;
      try {
        user = userStr ? JSON.parse(userStr) : null;
      } catch {
        user = null;
      }
      
      set({
        user,
        token,
        refreshToken,
        isAuthenticated: true,
      });
    }
  },
}));