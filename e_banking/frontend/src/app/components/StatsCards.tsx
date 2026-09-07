import { TrendingDown, ShieldCheck, CreditCard } from 'lucide-react';

interface StatsCardsProps {
  todaySpent: number;
  dailyLimit: number;
  transactionCount: number;
}

export function StatsCards({ todaySpent, dailyLimit, transactionCount }: StatsCardsProps) {
  const remaining = dailyLimit - todaySpent;

  const stats = [
    {
      label: 'Spent Today',
      value: `৳${todaySpent.toFixed(2)}`,
      icon: TrendingDown,
      iconColor: 'text-rose-600',
      bgColor: 'bg-rose-50/60',
      borderColor: 'border-slate-200/60 hover:border-rose-200/50',
    },
    {
      label: 'Remaining Limit',
      value: `৳${remaining.toFixed(2)}`,
      icon: ShieldCheck,
      iconColor: 'text-blue-600',
      bgColor: 'bg-blue-50/60',
      borderColor: 'border-slate-200/60 hover:border-blue-200/50',
    },
    {
      label: 'Transactions Count',
      value: String(transactionCount),
      icon: CreditCard,
      iconColor: 'text-emerald-600',
      bgColor: 'bg-emerald-50/60',
      borderColor: 'border-slate-200/60 hover:border-emerald-200/50',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-1 lg:h-full gap-4">
      {stats.map((stat) => {
        const Icon = stat.icon;
        return (
          <div
            key={stat.label}
            className={`bg-white border ${stat.borderColor} rounded-2xl p-5 shadow-sm hover:shadow-md transition-all duration-300 flex justify-between items-center`}
          >
            <div className="space-y-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">{stat.label}</span>
              <p className="text-xl md:text-2xl font-extrabold text-slate-800 tracking-tight font-sans select-none">{stat.value}</p>
            </div>
            <div className={`w-9 h-9 rounded-xl ${stat.bgColor} flex items-center justify-center shrink-0`}>
              <Icon className={stat.iconColor} size={18} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

