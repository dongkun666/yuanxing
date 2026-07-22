import { useNavigate, useLocation } from 'react-router-dom';
import { useUserStore } from '../../store';

interface SidebarItem {
  id: string;
  name: string;
  icon: string;
  path: string;
}

const MENU_ITEMS: SidebarItem[] = [
  { id: 'workstation', name: '工作台', icon: 'mdi:briefcase-outline', path: '/workstation' },
  { id: 'cases', name: '案件列表', icon: 'mdi:folder-multiple-outline', path: '/cases' },
  { id: 'contract-review', name: '合同审查', icon: 'mdi:file-document-check-outline', path: '/contract-review' },
];

export default function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useUserStore();

  const isActive = (path: string) => location.pathname === path;

  return (
    <aside className="w-56 bg-white border-r border-bg-border flex flex-col">
      <div className="p-4 border-b border-bg-border">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-brand flex items-center justify-center text-white text-lg">
            ⚖
          </div>
          <div>
            <h1 className="font-bold text-sm">LexPrime</h1>
            <p className="text-[10px] text-fg-tertiary">元枢法智</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-3 space-y-1">
        {MENU_ITEMS.map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => navigate(item.path)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all ${
              isActive(item.path)
                ? 'bg-brand-tint3 text-brand font-medium'
                : 'text-fg-secondary hover:bg-bg-subtle hover:text-fg-primary'
            }`}
          >
            <span className="iconify text-base" data-icon={item.icon} />
            <span>{item.name}</span>
          </button>
        ))}
      </nav>

      <div className="p-3 border-t border-bg-border">
        <div className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-bg-subtle transition-colors cursor-pointer">
          {user?.avatarUrl ? (
            <img src={user.avatarUrl} alt={user.name} className="w-8 h-8 rounded-full" />
          ) : (
            <div className="w-8 h-8 rounded-full bg-brand-tint3 flex items-center justify-center text-brand text-sm font-medium">
              {user?.name?.charAt(0) || 'U'}
            </div>
          )}
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-fg-primary truncate">{user?.name || '用户'}</p>
            <p className="text-[10px] text-fg-tertiary truncate">{user?.email}</p>
          </div>
          <button
            type="button"
            onClick={logout}
            className="text-fg-tertiary hover:text-danger transition-colors p-1"
            title="退出登录"
          >
            <span className="iconify text-sm" data-icon="mdi:logout" />
          </button>
        </div>
      </div>
    </aside>
  );
}