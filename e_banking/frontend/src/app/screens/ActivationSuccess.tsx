import { useNavigate, useLocation } from 'react-router';
import { Button } from '../components/Button';
import { CheckCircle, Shield, TrendingDown } from 'lucide-react';
import { motion } from 'motion/react';

export function ActivationSuccess() {
  const navigate = useNavigate();
  const location = useLocation();
  const { username } = location.state || {};

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#EFF6FF] to-white flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', duration: 0.6 }}
            className="inline-flex items-center justify-center w-24 h-24 bg-emerald-500 rounded-full mb-4"
          >
            <CheckCircle size={48} className="text-white" />
          </motion.div>
          <h1 className="mb-2">Account Activated</h1>
          <p className="text-muted-foreground">
            Your e-payment account is ready to use
          </p>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-lg border border-border mb-6 space-y-4">
          <div className="flex items-center justify-between pb-4 border-b border-border">
            <span className="text-muted-foreground">Username</span>
            <span className="font-semibold">@{username || 'user'}</span>
          </div>

          <div className="flex items-center justify-between pb-4 border-b border-border">
            <span className="text-muted-foreground">Daily Transaction Limit</span>
            <span className="font-semibold text-[#2563EB]">৳5,000.00</span>
          </div>

          <div className="bg-[#EFF6FF] rounded-lg p-4">
            <h4 className="mb-3 flex items-center gap-2">
              <Shield size={18} className="text-[#2563EB]" />
              Security Features Enabled
            </h4>
            <div className="space-y-2 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-emerald-500 rounded-full" />
                <span>AES Encryption</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-emerald-500 rounded-full" />
                <span>HMAC Authentication</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-emerald-500 rounded-full" />
                <span>Device-Bound Key (K1)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-emerald-500 rounded-full" />
                <span>Biometric Protection (BP)</span>
              </div>
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <TrendingDown size={20} className="text-blue-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-blue-900 mb-1">
                  Daily Petty Cash System
                </p>
                <p className="text-xs text-blue-800">
                  Your account supports small monetary transactions with a daily limit. The limit resets every 24 hours.
                </p>
              </div>
            </div>
          </div>
        </div>

        <Button fullWidth onClick={() => navigate('/login')}>
          Go to Login
        </Button>

        <div className="mt-8 text-center">
          <p className="text-xs text-muted-foreground">
            No OTP required • Device + Biometric + Password authentication
          </p>
        </div>
      </div>
    </div>
  );
}
