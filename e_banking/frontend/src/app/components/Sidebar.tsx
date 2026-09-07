import { useNavigate, useLocation } from 'react-router';
import { clearUserSession } from '../../utils/session';
import { 
  LayoutDashboard, Send, Store, Smartphone, Receipt, QrCode, 
  History, User, ShieldAlert, Settings, LogOut 
} from 'lucide-react';
import { SecurityBadge } from './SecurityBadge';

export function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    clearUserSession();
    navigate('/login');
  };

  const navItems = [
    { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { label: 'Send Money', path: '/send-money', icon: Send },
    { label: 'Merchant', path: '/merchant', icon: Store },
    { label: 'Recharge', path: '/recharge', icon: Smartphone },
    { label: 'Bills', path: '/bills', icon: Receipt },
    { label: 'My QR', path: '/my-qr', icon: QrCode },
    { label: 'History', path: '/history', icon: History },
    { label: 'Profile', path: '/profile', icon: User },
    { label: 'Security', path: '/security', icon: ShieldAlert },
    { label: 'Settings', path: '/settings', icon: Settings },
  ];

  return (
    <aside className="w-[260px] h-screen bg-white border-r border-slate-200 flex flex-col justify-between p-6">
      <div className="space-y-6">
        <div className="flex items-center gap-3 px-2">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center text-white font-black text-xl shadow-lg shadow-blue-500/15 select-none">
            N
          </div>
          <div>
            <span className="font-black text-base tracking-tight text-slate-900 block leading-none font-sans">NIROPAY</span>
            <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest block mt-1 font-sans">Secure Payments</span>
          </div>
        </div>

        <div className="px-2">
          <SecurityBadge type="device-verified" className="w-full justify-center" />
        </div>

        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <button
                key={item.label}
                onClick={() => navigate(item.path, { state: item.state })}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors cursor-pointer ${
                  isActive 
                    ? 'bg-blue-50 text-blue-600' 
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                }`}
              >
                <Icon size={18} className={isActive ? 'text-blue-600' : 'text-slate-400'} />
                {item.label}
              </button>
            );
          })}
        </nav>
      </div>

      <button
        onClick={handleLogout}
        className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-red-600 hover:bg-red-50 transition-colors cursor-pointer"
      >
        <LogOut size={18} className="text-red-500" />
        Logout
      </button>
    </aside>
  );
}
