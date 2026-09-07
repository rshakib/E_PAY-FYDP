import { ArrowUpRight, ArrowDownLeft, CheckCircle, XCircle, Clock } from 'lucide-react';
import { SecurityBadge } from './SecurityBadge';

interface TransactionCardProps {
  receiverUsername?: string;
  senderUsername?: string;
  amount: number;
  timestamp: string;
  status: 'success' | 'rejected' | 'pending' | 'aborted' | 'futile';
  showSecurityBadge?: boolean;
  type?: 'sent' | 'received';
}

export function TransactionCard({
  receiverUsername,
  senderUsername,
  amount,
  timestamp,
  status,
  showSecurityBadge = true,
  type = 'sent',
}: TransactionCardProps) {
  const isReceived = type === 'received';

  const statusConfig = {
    success: {
      icon: CheckCircle,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-50',
      label: 'Success',
    },
    rejected: {
      icon: XCircle,
      color: 'text-red-600',
      bgColor: 'bg-red-50',
      label: 'Failed',
    },
    aborted: {
      icon: XCircle,
      color: 'text-red-600',
      bgColor: 'bg-red-50',
      label: 'Failed',
    },
    futile: {
      icon: XCircle,
      color: 'text-red-600',
      bgColor: 'bg-red-50',
      label: 'Failed',
    },
    pending: {
      icon: Clock,
      color: 'text-amber-600',
      bgColor: 'bg-amber-50',
      label: 'Pending',
    },
  };

  const normalizedStatus = statusConfig[status] ? status : 'rejected';
  const config = statusConfig[normalizedStatus as keyof typeof statusConfig];
  const StatusIcon = config.icon;

  return (
    <div className="bg-white border border-slate-100 rounded-xl p-2.5 hover:bg-slate-50/70 hover:shadow-sm transition-all duration-200">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${isReceived ? 'bg-emerald-50 text-emerald-600' : 'bg-blue-50 text-blue-600'}`}>
            {isReceived ? <ArrowDownLeft size={16} /> : <ArrowUpRight size={16} />}
          </div>
          <div>
            <p className="font-bold text-xs text-slate-800">
              {isReceived ? `From @${senderUsername || 'unknown'}` : `To @${receiverUsername || 'unknown'}`}
            </p>
            <p className="text-[10px] text-slate-400 font-semibold mt-0.5">{timestamp}</p>
          </div>
        </div>
        <div className="text-right">
          <p className={`font-black text-sm tracking-tight ${isReceived ? 'text-emerald-600' : 'text-slate-800'}`}>
            {isReceived ? '+' : '-'}৳{amount.toFixed(2)}
          </p>
          <div className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md ${config.bgColor} mt-0.5`}>
            <StatusIcon size={9} className={config.color} />
            <span className={`text-[9px] font-black uppercase tracking-wider ${config.color}`}>{config.label}</span>
          </div>
        </div>
      </div>
      {showSecurityBadge && status === 'success' && (
        <div className="flex gap-1.5 mt-2 pt-2 border-t border-slate-100 flex-wrap">
          <SecurityBadge type="aes-secured" className="text-[9px]" />
          <SecurityBadge type="hmac-verified" className="text-[9px]" />
        </div>
      )}
    </div>
  );
}

