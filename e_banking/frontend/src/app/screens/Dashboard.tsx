import { useEffect, useState } from 'react';
import { useNavigate, Navigate } from 'react-router';
import { TransactionCard } from '../components/TransactionCard';
import {
  Send,
  Sparkles,
  Store,
  Smartphone,
  Receipt,
  ArrowUpRight,
  QrCode,
  History,
  User,
} from 'lucide-react';
import { getUserSession } from '../../utils/session';
import { getTransactionHistory } from '../../utils/api';
import { Sidebar } from '../components/Sidebar';
import { Navbar } from '../components/Navbar';
import { BalanceCard } from '../components/BalanceCard';
import { StatsCards } from '../components/StatsCards';

interface DashboardTransaction {
  receiver_username?: string;
  sender_username?: string;
  receiverUsername?: string;
  amount: number;
  created_at?: string;
  timestamp?: string;
  status: 'success' | 'aborted' | 'futile' | 'rejected';
  type?: 'sent' | 'received';
}

export function Dashboard() {
  const navigate = useNavigate();
  const session = getUserSession();
  const [recentTransactions, setRecentTransactions] = useState<DashboardTransaction[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const quickActions = [
    { label: 'Send Money', icon: Send, iconBg: 'bg-blue-50 text-blue-600 group-hover:bg-blue-600 group-hover:text-white', path: '/send-money' },
    { label: 'Merchant', icon: Store, iconBg: 'bg-emerald-50 text-emerald-600 group-hover:bg-emerald-600 group-hover:text-white', path: '/merchant' },
    { label: 'Recharge', icon: Smartphone, iconBg: 'bg-amber-50 text-amber-600 group-hover:bg-amber-600 group-hover:text-white', path: '/recharge' },
    { label: 'Bills', icon: Receipt, iconBg: 'bg-indigo-50 text-indigo-600 group-hover:bg-indigo-600 group-hover:text-white', path: '/bills' },
    { label: 'Cash Out', icon: ArrowUpRight, iconBg: 'bg-rose-50 text-rose-600 group-hover:bg-rose-600 group-hover:text-white', path: '/cashout' },
    { label: 'QR Pay', icon: QrCode, iconBg: 'bg-cyan-50 text-cyan-600 group-hover:bg-cyan-600 group-hover:text-white', path: '/qr-pay' },
    { label: 'History', icon: History, iconBg: 'bg-violet-50 text-violet-600 group-hover:bg-violet-600 group-hover:text-white', path: '/history' },
    { label: 'Profile', icon: User, iconBg: 'bg-slate-50 text-slate-600 group-hover:bg-slate-600 group-hover:text-white', path: '/profile' },
  ];

  useEffect(() => {
    let cancelled = false;
    async function loadRecentTransactions() {
      if (!session) return;
      const result = await getTransactionHistory(session.username);
      if (!cancelled && result?.transactions) {
        setRecentTransactions(result.transactions.slice(0, 3));
      }
    }
    loadRecentTransactions();
    return () => {
      cancelled = true;
    };
  }, [session?.username]);

  if (!session) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen grid lg:grid-cols-[260px_1fr] bg-slate-50 font-sans">
      {/* Sidebar for Desktop */}
      <div className="hidden lg:block">
        <Sidebar />
      </div>

      {/* Mobile / Tablet Drawer Sidebar Overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm" onClick={() => setSidebarOpen(false)} />
          <div className="relative z-50 animate-in slide-in-from-left duration-200">
            <Sidebar />
          </div>
        </div>
      )}

      {/* Main Content Workspace */}
      <div className="flex flex-col min-h-screen overflow-x-hidden">
        <Navbar onMenuToggle={() => setSidebarOpen(true)} />
        
        <main className="flex-1 p-6 space-y-6 max-w-5xl w-full mx-auto">
          {/* Row 1: Balance & Statistics */}
          <div className="grid grid-cols-1 lg:grid-cols-[58%_42%] gap-6 items-stretch">
            <BalanceCard 
              balance={session.balance} 
              todaySpent={session.today_spent} 
              dailyLimit={session.daily_limit} 
            />
            <StatsCards 
              todaySpent={session.today_spent} 
              dailyLimit={session.daily_limit} 
              transactionCount={recentTransactions.length} 
            />
          </div>

          {/* Row 2: Quick Actions & Recent Transactions */}
          <div className="grid grid-cols-1 lg:grid-cols-[1fr_420px] gap-6 items-stretch">
            {/* Quick Actions */}
            <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-200 flex flex-col justify-between">
              <h3 className="mb-4 text-slate-800 font-extrabold text-lg tracking-tight">Quick Actions</h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5 flex-1">
                {quickActions.map((action, index) => {
                  const Icon = action.icon;
                  return (
                    <button
                      key={index}
                      onClick={() => navigate(action.path, { state: action.state })}
                      className="flex flex-col items-center justify-center gap-3.5 p-4 rounded-2xl border border-slate-200/60 bg-white hover:border-blue-600/30 hover:shadow-md transition-all duration-300 group cursor-pointer active:scale-95"
                    >
                      <div className={`w-12 h-12 rounded-2xl flex items-center justify-center transition-all duration-300 ${action.iconBg}`}>
                        <Icon size={20} className="transition-transform duration-300 group-hover:scale-110" />
                      </div>
                      <span className="text-[11px] font-bold text-slate-600 group-hover:text-slate-900 transition-colors tracking-tight text-center">
                        {action.label}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Recent Activity Feed */}
            <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-200 flex flex-col justify-between">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-slate-800 font-extrabold text-lg tracking-tight">Recent Activity</h3>
                <button
                  onClick={() => navigate('/history')}
                  className="text-xs font-bold text-blue-600 hover:text-blue-700 transition-colors hover:underline cursor-pointer"
                >
                  View All
                </button>
              </div>
              <div className="flex-1 flex flex-col justify-center">
                {recentTransactions.length > 0 ? (
                  <div className="space-y-3">
                    {recentTransactions.map((transaction, index) => (
                      <TransactionCard
                        key={index}
                        type={transaction.type}
                        senderUsername={transaction.sender_username || transaction.senderUsername}
                        receiverUsername={transaction.receiver_username || transaction.receiverUsername}
                        amount={transaction.amount}
                        timestamp={transaction.created_at || transaction.timestamp || ''}
                        status={transaction.status === 'success' ? 'success' : 'rejected'}
                        showSecurityBadge={false}
                      />
                    ))}
                  </div>
                ) : (
                  <div className="rounded-2xl border border-dashed border-slate-200 p-6 text-center">
                    <p className="text-xs font-medium text-slate-400">No transactions yet</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Additional Features Banner */}
          <button
            onClick={() => navigate('/features')}
            className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-3xl p-6 shadow-md hover:shadow-lg transition-all duration-300 cursor-pointer active:scale-[0.99]"
          >
            <div className="flex items-center justify-between">
              <div className="text-left">
                <div className="flex items-center gap-2 mb-1">
                  <Sparkles size={20} className="text-blue-100" />
                  <h4 className="text-white font-extrabold tracking-tight">Additional Features</h4>
                </div>
                <p className="text-xs text-blue-100/90 font-medium">Email, QR, NFC, Cards & Social Login</p>
              </div>
              <div className="text-2xl font-bold">→</div>
            </div>
          </button>
        </main>
      </div>
    </div>
  );
}
