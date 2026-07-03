import { apiClient, requestWithRetry } from './client';
import type { RiskClause, Stance } from '../types';

export interface ContractReviewRequest {
  file: File;
  stance: Stance;
}

export interface ContractReviewResponse {
  clauses: RiskClause[];
  fileName: string;
  totalFatal: number;
  totalMajor: number;
  totalOk: number;
}

export interface ExportRequest {
  clauseIds: string[];
  format: 'pdf' | 'docx' | 'json';
}

export const contractApi = {
  review: async (file: File, stance: Stance): Promise<ContractReviewResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('stance', stance);
    
    const response = await requestWithRetry(() =>
      apiClient.post('/api/contract-review/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    );
    return response.data;
  },

  export: async (clauseIds: string[], format: ExportRequest['format']): Promise<Blob> => {
    const response = await requestWithRetry(() =>
      apiClient.post('/api/contract-review/export', { clauseIds, format }, {
        responseType: 'blob',
      })
    );
    return response.data;
  },

  getTemplates: async (): Promise<{ id: string; name: string; category: string }[]> => {
    const response = await requestWithRetry(() =>
      apiClient.get('/api/contract-review/templates')
    );
    return response.data;
  },
};