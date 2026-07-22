import { apiClient, requestWithRetry } from './client';
import type { Case } from '../types';

export interface CaseListResponse {
  data: Case[];
  total: number;
  page: number;
  pageSize: number;
}

export interface CreateCaseRequest {
  name: string;
  role: Case['role'];
  filedAt: string;
  description?: string;
}

export const caseApi = {
  list: async (page: number = 1, pageSize: number = 10): Promise<CaseListResponse> => {
    const response = await requestWithRetry(() =>
      apiClient.get('/api/cases', { params: { page, pageSize } })
    );
    return response.data;
  },

  get: async (id: string): Promise<Case> => {
    const response = await requestWithRetry(() =>
      apiClient.get(`/api/cases/${id}`)
    );
    return response.data;
  },

  create: async (data: CreateCaseRequest): Promise<Case> => {
    const response = await requestWithRetry(() =>
      apiClient.post('/api/cases', data)
    );
    return response.data;
  },

  update: async (id: string, data: Partial<CreateCaseRequest>): Promise<Case> => {
    const response = await requestWithRetry(() =>
      apiClient.put(`/api/cases/${id}`, data)
    );
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await requestWithRetry(() =>
      apiClient.delete(`/api/cases/${id}`)
    );
  },

  search: async (keyword: string): Promise<Case[]> => {
    const response = await requestWithRetry(() =>
      apiClient.get('/api/cases/search', { params: { keyword } })
    );
    return response.data;
  },
};