import { ipcMain, dialog, shell } from 'electron';
import { writeFileSync } from 'node:fs';

export function registerIpcHandlers(mainWindow: Electron.BrowserWindow | null): void {
  ipcMain.handle('app:version', () => process.env.npm_package_version || '0.0.0');

  ipcMain.handle('app:platform', () => ({
    platform: process.platform,
    arch: process.arch,
    electron: process.versions.electron,
    chrome: process.versions.chrome,
    node: process.versions.node,
  }));

  ipcMain.handle('app:check-update', async () => {
    if (!process.env.NODE_ENV || process.env.NODE_ENV === 'development') {
      return { ok: false, reason: 'dev 模式跳过' };
    }
    return { ok: true, version: process.env.npm_package_version };
  });

  ipcMain.handle('app:export-data', async (_evt, payload: unknown) => {
    if (!mainWindow) return { ok: false };
    const { canceled, filePath } = await dialog.showSaveDialog(mainWindow, {
      title: '导出案件数据',
      defaultPath: `lexprime-case-${Date.now()}.json`,
      filters: [{ name: 'JSON', extensions: ['json'] }],
    });
    if (canceled || !filePath) return { ok: false, reason: 'cancelled' };
    try {
      writeFileSync(filePath, JSON.stringify(payload, null, 2), 'utf-8');
      return { ok: true, path: filePath };
    } catch (err) {
      return { ok: false, reason: String(err) };
    }
  });

  ipcMain.handle('app:open-user-data', (_evt) => {
    const { app } = require('electron');
    shell.openPath(app.getPath('userData')).catch(console.error);
  });
}