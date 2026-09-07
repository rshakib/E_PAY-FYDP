import { useNavigate, useLocation } from 'react-router';
import { Button } from '../components/Button';
import { SecurityBadge } from '../components/SecurityBadge';
import { CheckCircle, XCircle, Shield, AlertTriangle } from 'lucide-react';
import { motion } from 'motion/react';

export function TransactionResult() {
  const navigate = useNavigate();
  const location = useLocation();
  const { receiverUsername, amount, timestamp, status = 'success', newBalance, errorMessage } = location.state || {};

  if (!receiverUsername || !amount) {
    navigate('/dashboard');
    return null;
  }

  const calculatedBalance = newBalance !== undefined ? newBalance : undefined;
  const newTimestamp = new Date().toLocaleString('en-GB', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });

  const statusConfig = {
    success: {
      icon: CheckCircle,
      color: 'text-emerald-500',
      bgColor: 'bg-emerald-100',
      title: 'Transaction Successful',
      message: 'Your payment has been processed securely',
    },
    hmac_mismatch: {
      icon: XCircle,
      color: 'text-destructive',
      bgColor: 'bg-red-100',
      title: 'HMAC Mismatch — Transaction Rejected',
      message: 'Message integrity check failed (F1 ≠ F2)',
    },
    insufficient_balance: {
      icon: AlertTriangle,
      color: 'text-amber-500',
      bgColor: 'bg-amber-100',
      title: 'Insufficient Balance — Transaction Aborted',
      message: 'Your account balance is insufficient for this transaction',
    },
    receiver_not_found: {
      icon: XCircle,
      color: 'text-destructive',
      bgColor: 'bg-red-100',
      title: 'Receiver Not Found in Database',
      message: 'The receiver username does not exist in our system',
    },
    self_transaction: {
      icon: AlertTriangle,
      color: 'text-amber-500',
      bgColor: 'bg-amber-100',
      title: 'Self Transaction Not Allowed',
      message: 'Please enter another receiver username to continue.',
    },
    error: {
      icon: AlertTriangle,
      color: 'text-red-500',
      bgColor: 'bg-red-100',
      title: 'Transaction Failed',
      message: 'An error occurred while processing your transaction. Please try again.',
    },
  };

  const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.error;
  const Icon = config?.icon || AlertTriangle;
  const isSuccess = status === 'success';

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="max-w-2xl w-full bg-white rounded-2xl p-8 shadow-lg border border-border"
      >
        <div className="text-center mb-8">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', duration: 0.6 }}
            className={`inline-flex items-center justify-center w-24 h-24 ${config.bgColor} rounded-full mb-4`}
          >
            <Icon size={48} className={config.color} />
          </motion.div>
          <h1 className="mb-2">{config.title}</h1>
          <p className="text-muted-foreground">{config.message}</p>
          {errorMessage && (
            <p className="text-sm text-red-600 mt-2">Details: {errorMessage}</p>
          )}
        </div>

        {isSuccess && (
          <div className="mb-6 flex justify-center gap-3">
            <SecurityBadge type="hmac-verified" />
            <SecurityBadge type="aes-secured" />
          </div>
        )}

        <div className="bg-[#EFF6FF] rounded-xl p-6 mb-6 space-y-3">
          <div className="flex items-center justify-between pb-3 border-b border-border">
            <span className="text-muted-foreground">Sent to:</span>
            <span className="font-semibold">@{receiverUsername}</span>
          </div>
          <div className="flex items-center justify-between pb-3 border-b border-border">
            <span className="text-muted-foreground">Amount:</span>
            <span className="font-semibold text-lg">৳{amount.toFixed(2)}</span>
          </div>
          {isSuccess && calculatedBalance !== undefined && (
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <span className="text-muted-foreground">New Balance:</span>
              <span className="font-semibold text-[#2563EB]">৳{calculatedBalance.toFixed(2)}</span>
            </div>
          )}
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Timestamp {isSuccess ? 'Updated (T)' : ''}:</span>
            <span className="font-mono text-sm">{isSuccess ? newTimestamp : timestamp}</span>
          </div>
        </div>

        {isSuccess ? (
          <div className="bg-white border border-border rounded-xl p-4 mb-6">
            <div className="flex items-start gap-3">
              <Shield size={20} className="text-[#2563EB] flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="mb-1">Cryptographic Verification Complete</h4>
                <p className="text-sm text-muted-foreground">
                  Server-side HMAC check passed: <span className="font-mono text-[#2563EB]">F1 = F2</span>
                </p>
                <p className="text-xs text-muted-foreground mt-2">
                  Message integrity verified • AES decryption successful • Transaction committed
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6">
            <p className="text-sm text-red-900">
              Only you have been notified of this failure. The transaction was not processed.
            </p>
          </div>
        )}

        <Button fullWidth onClick={() => navigate('/dashboard')}>
          Back to Home
        </Button>

        <div className="mt-4 text-center">
          <button
            onClick={() => navigate('/history')}
            className="text-sm text-[#2563EB] hover:underline"
          >
            View Transaction History
          </button>
        </div>
      </motion.div>
    </div>
  );
}
