/**
 * LexPrime 元枢法智 · Electron Preload Script
 *
 * Phase 5.2 预加载脚本 - 暴露安全的 IPC API 给 renderer (React)
 * 使用 contextBridge + sandbox, 不暴露 Node API 给页面
 */
import { contextBridge, ipcRenderer } from 'electron';

// ===== 类型定义 (跟 main.ts IPC 保持一致) =====
export interface PlatformInfo {
  platform: NodeJS.Platform;
  arch: string;
  electron: string;
  chrome: string;
  node: string;
}

export interface UpdateAvailableInfo {
  version: string;
  releaseDate: string;
}

export interface UpdateProgressInfo {
  percent: number;
  transferred: number;
  total: number;
}

export interface UpdateDownloadedInfo {
  version: string;
  releaseDate: string;
}

// ===== ContextBridge API =====
const api = {
  /** 应用版本号 */
  getVersion: (): Promise<string> => ipcRenderer.invoke('app:version'),

  /** 平台信息 */
  getPlatform: (): Promise<PlatformInfo> => ipcRenderer.invoke('app:platform'),

  /** 触发 auto-update 检查 */
  checkUpdate: (): Promise<{ ok: boolean; version?: string; reason?: string }> =>
    ipcRenderer.invoke('app:check-update'),

  /** 导出案件数据到本地 */
  exportData: (payload: unknown): Promise<{ ok: boolean; path?: string; reason?: string }> =>
    ipcRenderer.invoke('app:export-data', payload),

  /** 打开用户数据目录 */
  openUserDataDir: (): Promise<void> => ipcRenderer.invoke('app:open-user-data'),

  // ===== 事件订阅 (auto-update) =====
  onUpdateChecking: (cb: () => void) => {
    const handler = () => cb();
    ipcRenderer.on('update:checking', handler);
    return () => ipcRenderer.removeListener('update:checking', handler);
  },

  onUpdateAvailable: (cb: (info: UpdateAvailableInfo) => void) => {
    const handler = (_e: unknown, info: UpdateAvailableInfo) => cb(info);
    ipcRenderer.on('update:available', handler);
    return () => ipcRenderer.removeListener('update:available', handler);
  },

  onUpdateNotAvailable: (cb: () => void) => {
    const handler = () => cb();
    ipcRenderer.on('update:not-available', handler);
    return () => ipcRenderer.removeListener('update:not-available', handler);
  },

  onUpdateProgress: (cb: (info: UpdateProgressInfo) => void) => {
    const handler = (_e: unknown, info: UpdateProgressInfo) => cb(info);
    ipcRenderer.on('update:progress', handler);
    return () => ipcRenderer.removeListener('update:progress', handler);
  },

  onUpdateDownloaded: (cb: (info: UpdateDownloadedInfo) => void) => {
    const handler = (_e: unknown, info: UpdateDownloadedInfo) => cb(info);
    ipcRenderer.on('update:downloaded', handler);
    return () => ipcRenderer.removeListener('update:downloaded', handler);
  },

  onUpdateError: (cb: (err: { message: string }) => void) => {
    const handler = (_e: unknown, err: { message: string }) => cb(err);
    ipcRenderer.on('update:error', handler);
    return () => ipcRenderer.removeListener('update:error', handler);
  },
} as const;

contextBridge.exposeInMainWorld('lexprime', api);

export type LexprimeAPI = typeof api;
