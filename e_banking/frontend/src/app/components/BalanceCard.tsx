import { useState } from 'react';
import { useNavigate } from 'react-router';
import { Eye, EyeOff, Send, ArrowUpRight } from 'lucide-react';
import { DailyLimitIndicator } from './DailyLimitIndicator';

interface BalanceCardProps {
  balance: number;
  todaySpent: number;
  dailyLimit: number;
}

export function BalanceCard({ balance, todaySpent, dailyLimit }: BalanceCardProps) {
  const navigate = useNavigate();
  const [showBalance, setShowBalance] = useState(true);

  return (
    <div className="relative overflow-hidden bg-gradient-to-br from-blue-600 via-blue-700 to-blue-800 rounded-3xl p-6 shadow-xl flex flex-col justify-between space-y-6 text-white border border-blue-500/30">
      {/* Decorative background shapes */}
      <div className="absolute top-0 right-0 -mt-6 -mr-6 w-32 h-32 bg-white/10 rounded-full blur-2xl pointer-events-none" />
      <div className="absolute -bottom-8 -left-8 w-40 h-40 bg-blue-500/20 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute top-1/2 left-1/3 w-24 h-24 bg-indigo-500/25 rounded-full blur-2xl pointer-events-none" />

      <div className="relative z-10 space-y-1">
        <span className="text-xs font-semibold tracking-wider text-blue-100/80 uppercase">Total Balance</span>
        <div className="flex items-center justify-between">
          <div className="text-3xl lg:text-4xl font-extrabold tracking-tight transition-all font-sans select-none">
            {showBalance ? `৳${balance.toFixed(2)}` : '৳••••••'}
          </div>
          <button
            onClick={() => setShowBalance(!showBalance)}
            className="p-2 bg-white/15 hover:bg-white/25 text-white rounded-xl transition-all cursor-pointer border border-white/10 flex items-center justify-center"
            title={showBalance ? "Hide Balance" : "Show Balance"}
          >
            {showBalance ? <Eye size={18} /> : <EyeOff size={18} />}
          </button>
        </div>
      </div>

      <div className="relative z-10 grid grid-cols-2 gap-3">
        <button
          onClick={() => navigate('/send-money')}
          className="flex items-center justify-center gap-2 py-3 bg-white hover:bg-blue-50 text-blue-700 rounded-2xl font-bold text-sm shadow-md transition-all duration-200 cursor-pointer active:scale-95"
        >
          <Send size={15} className="stroke-[2.5]" />
          Send Money
        </button>
        <button
          onClick={() => navigate('/cashout')}
          className="flex items-center justify-center gap-2 py-3 bg-white/10 hover:bg-white/20 border border-white/20 text-white rounded-2xl font-bold text-sm shadow-sm transition-all duration-200 cursor-pointer active:scale-95"
        >
          <ArrowUpRight size={16} className="stroke-[2.5]" />
          Cash Out
        </button>
      </div>

      <div className="relative z-10 border-t border-white/10 pt-4">
        <DailyLimitIndicator spent={todaySpent} limit={dailyLimit} showDetails={false} />
      </div>
    </div>
  );
}

