import { TrendingDown } from 'lucide-react';

interface DailyLimitIndicatorProps {
  spent: number;
  limit: number;
  showDetails?: boolean;
}

export function DailyLimitIndicator({ spent, limit, showDetails = true }: DailyLimitIndicatorProps) {
  const remaining = limit - spent;
  const percentage = (spent / limit) * 100;

  const getColor = () => {
    if (percentage >= 90) return 'bg-red-500';
    if (percentage >= 70) return 'bg-amber-400';
    return 'bg-emerald-400';
  };

  return (
    <div className="space-y-2.5">
      {showDetails && (
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <TrendingDown size={18} className="text-blue-100" />
            <span className="font-medium text-sm text-blue-100">Daily Petty Cash Limit</span>
          </div>
          <span className="text-xs font-semibold text-blue-200">
            {percentage.toFixed(0)}% used
          </span>
        </div>
      )}

      <div className="relative w-full h-2 bg-white/20 rounded-full overflow-hidden">
        <div
          className={`h-full ${getColor()} transition-all duration-500 rounded-full`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>

      <div className="flex items-center justify-between text-xs">
        <span className="text-blue-100">
          Spent: <span className="font-semibold text-white">৳{spent.toFixed(2)}</span>
        </span>
        <span className="text-blue-100">
          Remaining: <span className="font-semibold text-white">৳{remaining.toFixed(2)}</span>
        </span>
      </div>

      {showDetails && (
        <p className="text-[10px] text-blue-200/80">
          Total daily limit: ৳{limit.toFixed(2)}
        </p>
      )}
    </div>
  );
}

