import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router';
import { ProcessingStep } from '../components/ProcessingStep';
import { motion } from 'motion/react';
import { getUserSession, updateUserTimestamp, updateUserBalance } from '../../utils/session';
import { processTransfer } from '../../utils/api';

export function TransactionProcessing() {
  const navigate = useNavigate();
  const location = useLocation();
  const { receiverUsername, amount } = location.state || {};

  const [currentStep, setCurrentStep] = useState(-1);
  const [timestamp, setTimestamp] = useState('');
  const [transactionStatus, setTransactionStatus] = useState<'processing' | 'completed' | 'failed'>('processing');

  useEffect(() => {
    if (currentStep === -1) {
      const now = new Date();
      setTimestamp(now.toLocaleString('en-GB', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      }));
      startProcessing();
    }
  }, [currentStep]);

  const startProcessing = async () => {
    const session = getUserSession();
    if (!session) {
      navigate('/login');
      return;
    }

    setCurrentStep(0);

    try {
      // Step 1: Prepare transfer request
      setCurrentStep(1);
      await new Promise(resolve => setTimeout(resolve, 1500));

      // Step 2: Send to backend
      const response = await processTransfer(session.username, receiverUsername, amount);

      setCurrentStep(2);
      await new Promise(resolve => setTimeout(resolve, 1500));

      // Step 5: Handle response
      if (response.status === 'success' && response.new_t) {
        updateUserTimestamp(response.new_t);
        updateUserBalance(session.balance - amount);
        setTransactionStatus('completed');
        
        setTimeout(() => {
          navigate('/transaction-result', {
            state: {
              receiverUsername,
              amount,
              timestamp,
              status: 'success',
              newBalance: session.balance - amount,
            },
          });
        }, 1000);
      } else if (response.status === 'futile') {
        setTransactionStatus('failed');
        setTimeout(() => {
          navigate('/transaction-result', {
            state: {
              receiverUsername,
              amount,
              timestamp,
              status: 'insufficient_balance',
            },
          });
        }, 1000);
      } else {
        setTransactionStatus('failed');
        const statusMap: Record<string, string> = {
          'HMAC mismatch': 'hmac_mismatch',
          'User not found': 'receiver_not_found',
          'Self transaction not allowed': 'self_transaction',
        };
        const mappedStatus = Object.keys(statusMap).find(key => response.message.includes(key)) 
          ? statusMap[Object.keys(statusMap).find(key => response.message.includes(key))!]
          : 'error';
        
        setTimeout(() => {
          navigate('/transaction-result', {
            state: {
              receiverUsername,
              amount,
              timestamp,
              status: mappedStatus,
            },
          });
        }, 1000);
      }
    } catch (error) {
      console.error('Transaction error:', error);
      setTransactionStatus('failed');
      setTimeout(() => {
        navigate('/transaction-result', {
          state: {
            receiverUsername,
            amount,
            timestamp,
            status: 'error',
          },
        });
      }, 1000);
    }
  };

  if (!receiverUsername || !amount) {
    navigate('/dashboard');
    return null;
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-2xl w-full bg-white rounded-2xl p-8 shadow-lg border border-border"
        >
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ repeat: Infinity, duration: 2, ease: 'linear' }}
                className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full"
              />
            </div>
            <h2 className="mb-2">Processing Transaction</h2>
            <p className="text-muted-foreground">
              Secure transfer verification in progress
            </p>
          </div>

          <div className="bg-[#EFF6FF] rounded-xl p-6 mb-6">
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="text-muted-foreground">To:</span>
              <span className="font-semibold">@{receiverUsername}</span>
            </div>
            <div className="flex items-center justify-between text-sm mb-4">
              <span className="text-muted-foreground">Amount:</span>
              <span className="font-semibold text-[#2563EB]">৳{amount.toFixed(2)}</span>
            </div>
            {timestamp && (
              <div className="flex items-center justify-between text-xs border-t border-border pt-2">
                <span className="text-muted-foreground">Transaction Time (T):</span>
                <span className="font-mono text-[#2563EB]">{timestamp}</span>
              </div>
            )}
          </div>

          <ProcessingStep currentStep={currentStep} timestamp={timestamp} />

          <div className="mt-8 text-center">
            <p className="text-xs text-muted-foreground">
              Secret key material remains on the backend during transfer verification
            </p>
          </div>
      </motion.div>
    </div>
  );
}
