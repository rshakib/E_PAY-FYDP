import { Shield, CheckCircle, Lock, Hash } from 'lucide-react';

interface SecurityBadgeProps {
  type: 'device-verified' | 'hmac-verified' | 'aes-secured' | 'integrity-check';
  className?: string;
}

export function SecurityBadge({ type, className = '' }: SecurityBadgeProps) {
  const badges = {
    'device-verified': {
      icon: Shield,
      text: 'Device Verified',
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-50',
    },
    'hmac-verified': {
      icon: CheckCircle,
      text: 'HMAC Verified',
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    'aes-secured': {
      icon: Lock,
      text: 'AES Secured',
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    'integrity-check': {
      icon: Hash,
      text: 'Integrity Check',
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
  };

  const badge = badges[type];
  const Icon = badge.icon;

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full ${badge.bgColor} ${className}`}>
      <Icon size={16} className={badge.color} />
      <span className={`text-sm font-medium ${badge.color}`}>{badge.text}</span>
    </div>
  );
}
