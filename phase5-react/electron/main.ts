/**
 * LexPrime 元枢法智 · Electron 主进程
 *
 * Phase 5.2 (W20 10/1) 跨平台桌面端打包入口
 * - Windows: NSIS .exe 安装包
 * - macOS:   DMG 安装包 (Intel + Apple Silicon)
 * - Linux:   AppImage 安装包
 *
 * 集成 W19 phase5-react 3 模块:
 * - /login            → Login.tsx (登录)
 * - /workstation      → Workstation.tsx (工作站)
 * - /contract-review  → ContractReview.tsx (合同审查)
 *
 * 保留 5 大价值主张 + 6 大模块 (PRD V5.0 § 5-6, 不重写功能逻辑)
 */
import { app, BrowserWindow, ipcMain, Menu, shell, dialog } from 'electron';
import { autoUpdater } from 'electron-updater';
import { join } from 'node:path';
import { writeFileSync, existsSync, mkdirSync } from 'node:fs';

// ===== 全局状态 =====
const isDev = !app.isPackaged;
let mainWindow: BrowserWindow | null = null;

/** Phase 5.2 桌面端版本号 (跟 package.json 同步) */
const APP_VERSION = app.getVersion();
const APP_NAME = 'LexPrime 元枢法智';

/** dev server URL (Vite 5173) / prod dist 路径 */
const DEV_URL = process.env.VITE_DEV_SERVER_URL || 'http://127.0.0.1:5173';
const PROD_INDEX = join(__dirname, '..', 'dist', 'index.html');

// ===== 主窗口创建 =====
function createMainWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1024,
    minHeight: 720,
    title: APP_NAME,
    backgroundColor: '#F2F3F5',
    show: false,
    autoHideMenuBar: process.platform !== 'darwin',
    webPreferences: {
      preload: join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      webSecurity: true,
    },
  });

  // 加载 dev server / 生产 dist
  if (isDev) {
    mainWindow.loadURL(DEV_URL).catch((err) => {
      console.error('[main] failed to load dev server:', err);
      mainWindow?.loadFile(PROD_INDEX).catch((e) => {
        console.error('[main] failed to load prod fallback:', e);
      });
    });
  } else {
    mainWindow.loadFile(PROD_INDEX).catch((err) => {
      console.error('[main] failed to load prod dist:', err);
    });
  }

  // 外部链接走系统浏览器, 不在 Electron 内打开
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('https://') || url.startsWith('http://')) {
      shell.openExternal(url).catch(console.error);
    }
    return { action: 'deny' };
  });

  // 首次 ready-to-show 再显示, 避免白屏
  mainWindow.once('ready-to-show', () => {
    mainWindow?.show();
    if (isDev) {
      mainWindow?.webContents.openDevTools({ mode: 'detach' });
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// ===== 应用菜单 (macOS / Windows / Linux) =====
function buildAppMenu(): void {
  const isMac = process.platform === 'darwin';

  const template: Electron.MenuItemConstructorOptions[] = [
    ...(isMac
      ? [
          {
            label: APP_NAME,
            submenu: [
              { role: 'about' as const },
              { type: 'separator' as const },
              { role: 'services' as const },
              { type: 'separator' as const },
              { role: 'hide' as const },
              { role: 'hideOthers' as const },
              { role: 'unhide' as const },
              { type: 'separator' as const },
              { role: 'quit' as const },
            ],
          },
        ]
      : []),
    {
      label: '文件',
      submenu: [
        isMac ? { role: 'close' } : { role: 'quit' },
      ],
    },
    {
      label: '编辑',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
        { role: 'selectAll' },
      ],
    },
    {
      label: '视图',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' },
      ],
    },
    {
      label: '窗口',
      submenu: [
        { role: 'minimize' },
        { role: 'zoom' },
        ...(isMac
          ? [
              { type: 'separator' as const },
              { role: 'front' as const },
            ]
          : [{ role: 'close' as const }]),
      ],
    },
    {
      label: '帮助',
      submenu: [
        {
          label: '关于 LexPrime',
          click: () => {
            dialog.showMessageBox(mainWindow!, {
              type: 'info',
              title: '关于 LexPrime',
              message: APP_NAME,
              detail: `版本: v${APP_VERSION}\n` +
                `平台: ${process.platform} (${process.arch})\n` +
                `Electron: ${process.versions.electron}\n` +
                `Chromium: ${process.versions.chrome}\n` +
                `Node: ${process.versions.node}\n\n` +
                `法律 AI Agent 桌面端 · 律师单人版 MVP\n` +
                `AI 辅助不替代律师 · 5 大价值主张 · 6 大模块`,
            });
          },
        },
        {
          label: '访问官网',
          click: () => {
            shell.openExternal('https://lexprime.cn').catch(console.error);
          },
        },
      ],
    },
  ];

  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

// ===== IPC 处理器 (renderer ↔ main) =====
function registerIpcHandlers(): void {
  // 应用版本
  ipcMain.handle('app:version', () => APP_VERSION);

  // 平台信息
  ipcMain.handle('app:platform', () => ({
    platform: process.platform,
    arch: process.arch,
    electron: process.versions.electron,
    chrome: process.versions.chrome,
    node: process.versions.node,
  }));

  // 手动触发 auto-update 检查
  ipcMain.handle('app:check-update', async () => {
    if (isDev) {
      return { ok: false, reason: 'dev 模式跳过' };
    }
    try {
      const result = await autoUpdater.checkForUpdates();
      return { ok: true, version: result?.updateInfo.version };
    } catch (err) {
      return { ok: false, reason: String(err) };
    }
  });

  // 导出案件数据 (律师本地导出, 不走云)
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

  // 打开数据目录
  ipcMain.handle('app:open-user-data', () => {
    shell.openPath(app.getPath('userData')).catch(console.error);
  });
}

// ===== Auto-update 配置 (electron-updater) =====
function setupAutoUpdater(): void {
  if (isDev) {
    console.log('[main] dev 模式跳过 auto-update');
    return;
  }

  autoUpdater.autoDownload = false; // 用户确认后再下载
  autoUpdater.autoInstallOnAppQuit = true;

  autoUpdater.on('checking-for-update', () => {
    mainWindow?.webContents.send('update:checking');
  });

  autoUpdater.on('update-available', (info) => {
    mainWindow?.webContents.send('update:available', {
      version: info.version,
      releaseDate: info.releaseDate,
    });
  });

  autoUpdater.on('update-not-available', () => {
    mainWindow?.webContents.send('update:not-available');
  });

  autoUpdater.on('download-progress', (progress) => {
    mainWindow?.webContents.send('update:progress', {
      percent: progress.percent,
      transferred: progress.transferred,
      total: progress.total,
    });
  });

  autoUpdater.on('update-downloaded', (info) => {
    mainWindow?.webContents.send('update:downloaded', {
      version: info.version,
      releaseDate: info.releaseDate,
    });
    // 提示用户安装
    dialog
      .showMessageBox(mainWindow!, {
        type: 'info',
        title: '更新已下载',
        message: `LexPrime v${info.version} 已下载完成`,
        detail: '重启应用即可完成更新',
        buttons: ['立即重启', '稍后'],
        defaultId: 0,
        cancelId: 1,
      })
      .then(({ response }) => {
        if (response === 0) {
          autoUpdater.quitAndInstall();
        }
      });
  });

  autoUpdater.on('error', (err) => {
    console.error('[main] autoUpdater error:', err);
    mainWindow?.webContents.send('update:error', { message: err.message });
  });
}

// ===== 单实例锁 (避免多开) =====
const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });

  // ===== 应用生命周期 =====
  app.whenReady().then(() => {
    // 确保用户数据目录存在
    const userData = app.getPath('userData');
    if (!existsSync(userData)) {
      mkdirSync(userData, { recursive: true });
    }

    buildAppMenu();
    registerIpcHandlers();
    createMainWindow();
    setupAutoUpdater();

    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) {
        createMainWindow();
      }
    });
  });

  app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
      app.quit();
    }
  });

  // 安全: 阻止导航到外部 URL
  app.on('web-contents-created', (_evt, contents) => {
    contents.on('will-navigate', (e, url) => {
      const isDevUrl = url.startsWith(DEV_URL);
      const isFileUrl = url.startsWith('file://');
      if (!isDevUrl && !isFileUrl) {
        e.preventDefault();
        shell.openExternal(url).catch(console.error);
      }
    });
  });
}
