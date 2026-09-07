import { useState } from 'react';
import { useNavigate } from 'react-router';
import { Input } from '../components/Input';
import { Button } from '../components/Button';
import { ArrowLeft, AlertCircle, CheckCircle, Loader } from 'lucide-react';
import { getUserSession } from '../../utils/session';
import { checkReceiver } from '../../utils/api';


export function SendMoney() {
  const navigate = useNavigate();
  const session = getUserSession();

  const [formData, setFormData] = useState({
    receiverUsername: '',
    amount: '',
  });
  const [receiverFound, setReceiverFound] = useState<boolean | null>(null);
  const [searchingReceiver, setSearchingReceiver] = useState(false);

  if (!session) {
    navigate('/login');
    return null;
  }

  const dailyLimit = session.daily_limit;
  const spent = session.today_spent;
  const remaining = dailyLimit - spent;
  const normalizedReceiverUsername = formData.receiverUsername.trim().toLowerCase();
  const normalizedSessionUsername = session.username.trim().toLowerCase();
  const isSelfTransaction =
    normalizedReceiverUsername.length > 0 &&
    normalizedReceiverUsername === normalizedSessionUsername;

  const handleUsernameChange = async (value: string) => {
    setFormData({ ...formData, receiverUsername: value });
    const trimmedValue = value.trim();

    if (trimmedValue.toLowerCase() === normalizedSessionUsername) {
      setReceiverFound(false);
      setSearchingReceiver(false);
      return;
    }
    
    if (trimmedValue.length > 2) {
      setSearchingReceiver(true);
      try {
        const result = await checkReceiver(trimmedValue);
        setReceiverFound(result.found);
      } catch (error) {
        console.error('Error searching receiver:', error);
        setReceiverFound(false);
      } finally {
        setSearchingReceiver(false);
      }
    } else {
      setReceiverFound(null);
    }
  };


  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const amount = parseFloat(formData.amount);
    const receiverUsername = formData.receiverUsername.trim();

    if (receiverUsername.toLowerCase() === normalizedSessionUsername) {
      return;
    }

    if (amount > remaining) {
      alert(`Exceeds daily petty cash limit. Remaining: ৳${remaining.toFixed(2)}`);
      return;
    }

    if (receiverUsername && formData.amount && receiverFound) {
      navigate('/transaction-processing', {
        state: {
          receiverUsername,
          amount,
        },
      });
    }
  };

  const amountValue = parseFloat(formData.amount) || 0;
  const exceedsLimit = amountValue > remaining;

  return (
    <div className="min-h-screen bg-background">
      <div className="bg-[#2563EB] text-white px-4 py-6">
        <div className="max-w-2xl mx-auto flex items-center gap-4">
          <button
            onClick={() => navigate(-1)}
            className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center hover:bg-white/30 transition-colors"
          >
            <ArrowLeft size={20} />
          </button>
          <h1 className="text-white">Send Money</h1>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-6">
        <div className="bg-white rounded-2xl p-6 shadow-lg border border-border mb-4">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Input
                label="Receiver's Username"
                type="text"
                placeholder="Enter bank-assigned username"
                value={formData.receiverUsername}
                onChange={(e) => handleUsernameChange(e.target.value)}
                error={isSelfTransaction ? 'Self transaction not allowed. Please enter another receiver username.' : undefined}
                helperText="Username must be bank-assigned (not phone number)"
                required
              />
              {searchingReceiver && (
                <div className="mt-2 flex items-center gap-2 text-blue-600">
                  <Loader size={16} className="animate-spin" />
                  <span className="text-sm">Searching receiver...</span>
                </div>
              )}
              {receiverFound && !searchingReceiver && !isSelfTransaction && (
                <div className="mt-2 flex items-center gap-2 text-emerald-600">
                  <CheckCircle size={16} />
                  <span className="text-sm">Receiver found in database</span>
                </div>
              )}
              {receiverFound === false && !searchingReceiver && !isSelfTransaction && (
                <div className="mt-2 flex items-center gap-2 text-red-600">
                  <AlertCircle size={16} />
                  <span className="text-sm">Receiver not found</span>
                </div>
              )}
            </div>

            <div>
              <Input
                label="Amount (BDT)"
                type="number"
                placeholder="0.00"
                value={formData.amount}
                onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                error={exceedsLimit ? `Exceeds daily petty cash limit` : undefined}
                required
                min="1"
                step="0.01"
              />
              <div className="mt-2 text-sm text-muted-foreground">
                Daily limit remaining: <span className="font-semibold text-[#2563EB]">৳{remaining.toFixed(2)}</span>
              </div>
            </div>

            {exceedsLimit && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
                <AlertCircle size={20} className="text-red-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-red-900">
                    Amount exceeds daily petty cash limit
                  </p>
                  <p className="text-xs text-red-800 mt-1">
                    Maximum allowed: ৳{remaining.toFixed(2)}
                  </p>
                </div>
              </div>
            )}

            <Button type="submit" fullWidth disabled={exceedsLimit || isSelfTransaction || !receiverFound || searchingReceiver}>
              Proceed
            </Button>
          </form>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-blue-900 mb-2">Transfer Information</h4>
          <ul className="text-xs text-blue-800 space-y-1">
            <li>• Username-to-username transfer only</li>
            <li>• No phone number or bank account transfer</li>
            <li>• Default biometric fingerprint BP: 123456</li>
            <li>• Daily limit: ৳{dailyLimit.toFixed(2)}</li>
            <li>• Receiver must exist in Supabase database</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
