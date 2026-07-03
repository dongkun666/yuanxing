import { useState, useEffect } from 'react';
import { useUserStore } from '../../store';

declare global {
  interface Window {
    lexprime?: {
      getVersion: () => Promise<string>;
      getPlatform: () => Promise<{ platform: string; arch: string; electron: string; chrome: string; node: string }>;
      checkUpdate: () => Promise<{ ok: boolean; version?: string; reason?: string }>;
      onUpdateAvailable: (cb: (info: { version: string; releaseDate: string }) => void) => () => void;
    };
  }
}

interface HeaderProps {
  title: string;
  subtitle?: string;
}

export default function Header({ title, subtitle }: HeaderProps) {
  const { user } = useUserStore();
  const [version, setVersion] = useState('');
  const [updateAvailable, setUpdateAvailable] = useState(false);

  useEffect(() => {
    if (window.lexprime) {
      window.lexprime.getVersion().then(setVersion);
      window.lexprime.onUpdateAvailable((info) => {
        setUpdateAvailable(true);
        console.log('Update available:', info);
      });
    }
  }, []);

  const handleCheckUpdate = () => {
    window.lexprime?.checkUpdate().then((result) => {
      console.log('Check update result:', result);
      if (!result.ok) {
        alert(result.reason || '检查更新失败');
      }
    });
  };

  return (
    <header className="h-14 bg-white border-b border-bg-border flex items-center justify-between px-4">
      <div>
        <h2 className="font-bold text-base text-fg-primary">{title}</h2>
        {subtitle && <p className="text-[10px] text-fg-tertiary">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-4">
        {updateAvailable && (
          <button
            type="button"
            onClick={handleCheckUpdate}
            className="text-xs text-brand font-medium px-2 py-1 rounded bg-brand-tint3 hover:bg-brand-tint transition-colors"
          >
            有新版本可用
          </button>
        )}

        <div className="flex items-center gap-2">
          <span className="text-[10px] text-fg-tertiary">v{version}</span>
          <button
            type="button"
            onClick={handleCheckUpdate}
            className="text-fg-tertiary hover:text-fg-secondary transition-colors"
            title="检查更新"
          >
            <span className="iconify text-sm" data-icon="mdi:refresh" />
          </button>
        </div>

        {user && (
          <div className="flex items-center gap-2 pl-3 border-l border-bg-border">
            {user.avatarUrl ? (
              <img src={user.avatarUrl} alt={user.name} className="w-6 h-6 rounded-full" />
            ) : (
              <div className="w-6 h-6 rounded-full bg-brand-tint3 flex items-center justify-center text-brand text-xs font-medium">
                {user.name.charAt(0)}
              </div>
            )}
            <span className="text-xs text-fg-secondary">{user.name}</span>
          </div>
        )}
      </div>
    </header>
  );
}