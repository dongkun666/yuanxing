import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const BASE_URL = 'https://api.lexprime.com';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  async config => {
    const token = await AsyncStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  },
);

api.interceptors.response.use(
  response => response.data,
  async error => {
    if (error.response?.status === 401) {
      const refreshToken = await AsyncStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post(`${BASE_URL}/api/auth/refresh`, {
            refresh_token: refreshToken,
          });
          const {access_token, refresh_token} = response.data;
          await AsyncStorage.setItem('access_token', access_token);
          await AsyncStorage.setItem('refresh_token', refresh_token);
          error.config.headers.Authorization = `Bearer ${access_token}`;
          return api.request(error.config);
        } catch (refreshError) {
          await AsyncStorage.multiRemove(['access_token', 'refresh_token', 'user']);
        }
      }
    }
    return Promise.reject(error);
  },
);

export const casesApi = {
  getCases: (params = {}) => api.get('/api/cases', {params}),
  getCaseDetail: (docId) => api.get(`/api/cases/${docId}`),
  searchCases: (query, filters = {}) =>
    api.post('/api/search', {
      query,
      index: 'cases',
      page: 1,
      size: 20,
      filters,
    }),
  toggleFavorite: (docId) => api.post(`/api/cases/${docId}/favorite`),
  removeFavorite: (docId) => api.delete(`/api/cases/${docId}/favorite`),
  getFavorites: () => api.get('/api/cases/favorites'),
};

export const contractReviewApi = {
  uploadContract: (data) => api.post('/api/contract-review/upload', data),
  getResult: (reviewId) => api.get(`/api/contract-review/result/${reviewId}`),
  uploadFile: (formData) =>
    api.post('/api/contract-review/upload-file', formData, {
      headers: {'Content-Type': 'multipart/form-data'},
    }),
  ocrImage: (formData) =>
    api.post('/api/contract-review/ocr', formData, {
      headers: {'Content-Type': 'multipart/form-data'},
    }),
  exportReport: (reviewId, format) =>
    api.post('/api/contract-review/export', {review_id: reviewId, format}),
  getNegotiation: (reviewId, stance) =>
    api.post('/api/contract-review/negotiation', {review_id: reviewId, stance}),
};

export const scheduleApi = {
  getSchedule: (params = {}) => api.get('/api/schedule', {params}),
  getTodaySchedule: () => api.get('/api/schedule/today'),
  createSchedule: (data) => api.post('/api/schedule', data),
  updateSchedule: (id, data) => api.put(`/api/schedule/${id}`, data),
  deleteSchedule: (id) => api.delete(`/api/schedule/${id}`),
  checkConflicts: (params) => api.get('/api/schedule/conflicts', {params}),
};

export const authApi = {
  login: (email, password) =>
    api.post('/api/auth/login', {email, password}),
  register: (data) => api.post('/api/auth/register', data),
  logout: () => api.post('/api/auth/logout'),
  getCurrentUser: () => api.get('/api/users/me'),
  updateProfile: (data) => api.put('/api/users/me', data),
  refreshToken: (refreshToken) =>
    api.post('/api/auth/refresh', {refresh_token: refreshToken}),
  forgotPassword: (email) =>
    api.post('/api/auth/forgot-password', {email}),
  resetPassword: (token, password) =>
    api.post('/api/auth/reset-password', {token, password}),
};

export const aiApi = {
  chat: (message, conversationId) =>
    api.post('/api/ai/chat', {
      message,
      conversation_id: conversationId,
      stream: false,
    }),
  caseSummary: (data) => api.post('/api/ai/case-summary', data),
  polish: (content, options) =>
    api.post('/api/ai/polish', {content, options}),
  autoFill: (templateId, caseInfo) =>
    api.post('/api/ai/auto-fill', {template_id: templateId, case_info: caseInfo}),
};

export const notificationsApi = {
  getNotifications: (params = {}) => api.get('/api/notifications', {params}),
  getUnreadCount: () => api.get('/api/notifications/unread-count'),
  markAsRead: (id) => api.put(`/api/notifications/${id}/read`),
  markAllAsRead: () => api.put('/api/notifications/read-all'),
};

export const clientsApi = {
  getClients: (params = {}) => api.get('/api/clients', {params}),
  getClientDetail: (clientId) => api.get(`/api/clients/${clientId}`),
  createClient: (data) => api.post('/api/clients', data),
  updateClient: (clientId, data) => api.put(`/api/clients/${clientId}`, data),
  deleteClient: (clientId) => api.delete(`/api/clients/${clientId}`),
  checkConflict: (clientId) =>
    api.post(`/api/clients/${clientId}/conflict-check`),
  getStats: () => api.get('/api/clients/stats'),
};

export const gatewayApi = {
  getStats: () => api.get('/api/gateway/stats'),
  getUserStats: () => api.get('/api/gateway/user-stats'),
  registerDevice: (data) => api.post('/api/gateway/devices', data),
  syncData: (data) => api.post('/api/gateway/sync', data),
};

export default api;
