import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import { Bell, Search, Menu, User } from 'lucide-react';
import { getUserSession } from '../../utils/session';
import { getNotifications } from '../../utils/api';

interface NavbarProps {
  onMenuToggle?: () => void;
}

export function Navbar({ onMenuToggle }: NavbarProps) {
  const navigate = useNavigate();
  const session = getUserSession();
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    let cancelled = false;
    async function loadNotifications() {
      if (!session) return;
      const result = await getNotifications(session.username);
      if (!cancelled && result?.notifications) {
        const unread = result.notifications.filter((n: any) => !n.is_read).length;
        setUnreadCount(unread);
      }
    }
    loadNotifications();
    return () => {
      cancelled = true;
    };
  }, [session?.username]);

  return (
    <header className="h-[70px] bg-white border-b border-slate-200 px-6 flex items-center justify-between">
      <div className="flex items-center gap-4 flex-1">
        <button
          onClick={onMenuToggle}
          className="lg:hidden p-2 hover:bg-slate-100 rounded-lg text-slate-600 transition-colors cursor-pointer"
        >
          <Menu size={20} />
        </button>

        <div className="relative max-w-md w-full hidden sm:block">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
          <input
            type="text"
            placeholder="Search transactions, bills..."
            className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all"
          />
        </div>
      </div>

      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/notifications')}
          className="relative p-2 hover:bg-slate-100 rounded-lg text-slate-600 transition-colors cursor-pointer"
        >
          <Bell size={20} />
          {unreadCount > 0 && (
            <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full ring-2 ring-white" />
          )}
        </button>

        <button
          onClick={() => navigate('/profile')}
          className="flex items-center gap-3 pl-2 border-l border-slate-200 cursor-pointer hover:opacity-80 transition-opacity text-left bg-transparent border-0 focus:outline-none"
        >
          <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600">
            <User size={18} />
          </div>
          <div className="hidden md:block">
            <p className="text-sm font-semibold text-slate-900">@{session?.username || 'user'}</p>
            <p className="text-xs text-slate-500">Petty Cash Account</p>
          </div>
        </button>
      </div>
    </header>
  );
}
