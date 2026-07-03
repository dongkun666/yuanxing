import { create } from 'zustand';
import type { Case, RiskClause } from '../types';

interface CacheItem<T> {
  data: T;
  timestamp: number;
  expires: number;
}

interface CacheStore {
  cases: Map<string, CacheItem<Case[]>>;
  caseDetails: Map<string, CacheItem<Case>>;
  contractClauses: Map<string, CacheItem<RiskClause[]>>;
  
  setCases: (key: string, data: Case[], ttlMinutes?: number) => void;
  getCases: (key: string) => Case[] | null;
  setCaseDetail: (id: string, data: Case, ttlMinutes?: number) => void;
  getCaseDetail: (id: string) => Case | null;
  setContractClauses: (key: string, data: RiskClause[], ttlMinutes?: number) => void;
  getContractClauses: (key: string) => RiskClause[] | null;
  clearAll: () => void;
  clearExpired: () => void;
}

const DEFAULT_TTL = 60;

export const useCacheStore = create<CacheStore>((set, get) => ({
  cases: new Map(),
  caseDetails: new Map(),
  contractClauses: new Map(),

  setCases: (key, data, ttlMinutes = DEFAULT_TTL) => {
    const now = Date.now();
    const expires = now + ttlMinutes * 60 * 1000;
    const item: CacheItem<Case[]> = { data, timestamp: now, expires };
    set((state) => ({
      cases: new Map(state.cases).set(key, item),
    }));
  },

  getCases: (key) => {
    const item = get().cases.get(key);
    if (!item || Date.now() > item.expires) {
      return null;
    }
    return item.data;
  },

  setCaseDetail: (id, data, ttlMinutes = DEFAULT_TTL) => {
    const now = Date.now();
    const expires = now + ttlMinutes * 60 * 1000;
    const item: CacheItem<Case> = { data, timestamp: now, expires };
    set((state) => ({
      caseDetails: new Map(state.caseDetails).set(id, item),
    }));
  },

  getCaseDetail: (id) => {
    const item = get().caseDetails.get(id);
    if (!item || Date.now() > item.expires) {
      return null;
    }
    return item.data;
  },

  setContractClauses: (key, data, ttlMinutes = DEFAULT_TTL) => {
    const now = Date.now();
    const expires = now + ttlMinutes * 60 * 1000;
    const item: CacheItem<RiskClause[]> = { data, timestamp: now, expires };
    set((state) => ({
      contractClauses: new Map(state.contractClauses).set(key, item),
    }));
  },

  getContractClauses: (key) => {
    const item = get().contractClauses.get(key);
    if (!item || Date.now() > item.expires) {
      return null;
    }
    return item.data;
  },

  clearAll: () => {
    set({
      cases: new Map(),
      caseDetails: new Map(),
      contractClauses: new Map(),
    });
  },

  clearExpired: () => {
    const now = Date.now();
    set((state) => ({
      cases: new Map([...state.cases].filter(([, item]) => item.expires > now)),
      caseDetails: new Map([...state.caseDetails].filter(([, item]) => item.expires > now)),
      contractClauses: new Map([...state.contractClauses].filter(([, item]) => item.expires > now)),
    }));
  },
}));