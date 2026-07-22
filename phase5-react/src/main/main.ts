import { app, BrowserWindow, Menu, shell, dialog } from 'electron';
import { join } from 'node:path';
import { existsSync, mkdirSync } from 'node:fs';
import { registerIpcHandlers } from './ipc';
import { setupApiProxy } from './api-proxy';
import { setupAutoUpdater } from './auto-updater';

const isDev = !app.isPackaged;
let mainWindow: BrowserWindow | null = null;

const APP_VERSION = app.getVersion();
const APP_NAME = 'LexPrime 元枢法智';

const DEV_URL = process.env.VITE_DEV_SERVER_URL || 'http://127.0.0.1:5173';
const PROD_INDEX = join(__dirname, '..', 'dist', 'index.html');

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

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('https://') || url.startsWith('http://')) {
      shell.openExternal(url).catch(console.error);
    }
    return { action: 'deny' };
  });

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

  app.whenReady().then(() => {
    const userData = app.getPath('userData');
    if (!existsSync(userData)) {
      mkdirSync(userData, { recursive: true });
    }

    buildAppMenu();
    registerIpcHandlers(mainWindow);
    createMainWindow();
    setupAutoUpdater(mainWindow);
    setupApiProxy();

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