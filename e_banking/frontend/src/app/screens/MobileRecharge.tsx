import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import { Sidebar } from '../components/Sidebar';
import { Navbar } from '../components/Navbar';
import { Input } from '../components/Input';
import { Button } from '../components/Button';
import { 
  ArrowLeft, Smartphone, ChevronRight, Info, AlertCircle, 
  CheckCircle, Globe 
} from 'lucide-react';
import { getUserSession } from '../../utils/session';
import { getTransactionHistory } from '../../utils/api';

interface Operator {
  id: string;
  name: string;
  color: string;
  textColor: string;
  logoInitial: string;
  username: string;
}

export function MobileRecharge() {
  const navigate = useNavigate();
  const session = getUserSession();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [mobileNumber, setMobileNumber] = useState('');
  const [selectedOperator, setSelectedOperator] = useState<Operator | null>(null);
  const [amount, setAmount] = useState('');
  const [recentRecharges, setRecentRecharges] = useState<any[]>([]);

  const operators: Operator[] = [
    { id: 'gp', name: 'Grameenphone', color: 'bg-sky-500', textColor: 'text-white', logoInitial: 'GP', username: 'gp' },
    { id: 'robi', name: 'Robi', color: 'bg-red-600', textColor: 'text-white', logoInitial: 'R', username: 'robi' },
    { id: 'bl', name: 'Banglalink', color: 'bg-orange-500', textColor: 'text-white', logoInitial: 'BL', username: 'banglalink' },
    { id: 'airtel', name: 'Airtel', color: 'bg-rose-500', textColor: 'text-white', logoInitial: 'A', username: 'airtel' },
    { id: 'tt', name: 'Teletalk', color: 'bg-emerald-600', textColor: 'text-white', logoInitial: 'TT', username: 'teletalk' },
  ];

  const presets = [20, 50, 100, 200, 500];

  useEffect(() => {
    if (!session) {
      navigate('/login');
      return;
    }

    async function loadRecentRecharges() {
      try {
        const result = await getTransactionHistory(session!.username);
        if (result?.transactions) {
          // Filter recharges to operator_gp
          const rechargeTxns = result.transactions.filter((tx: any) => 
            tx.status === 'success' && 
            tx.type === 'sent' && 
            tx.receiver_username === 'operator_gp'
          );
          setRecentRecharges(rechargeTxns.slice(0, 5));
        }
      } catch (err) {
        console.error('Error loading recharge history:', err);
      }
    }

    loadRecentRecharges();
  }, [session?.username]);

  if (!session) {
    return null;
  }

  const dailyLimit = session.daily_limit;
  const spent = session.today_spent;
  const remaining = dailyLimit - spent;

  // Phone number validation: must start with 01 and be exactly 11 digits
  const isPhoneValid = /^01[3-9]\d{8}$/.test(mobileNumber);
  const showPhoneError = mobileNumber.length >= 11 && !isPhoneValid;

  const handleRecharge = (e: React.FormEvent) => {
    e.preventDefault();
    if (!isPhoneValid) {
      alert('Please enter a valid 11-digit Bangladeshi mobile number.');
      return;
    }

    if (!selectedOperator) {
      alert('Please select a mobile operator.');
      return;
    }

    const amtVal = parseFloat(amount);
    if (isNaN(amtVal) || amtVal < 10) {
      alert('Minimum recharge amount is BDT 10.');
      return;
    }

    if (amtVal > remaining) {
      alert(`Amount exceeds daily petty cash limit. Remaining: ৳${remaining.toFixed(2)}`);
      return;
    }

    navigate('/transaction-processing', {
      state: {
        receiverUsername: selectedOperator.username,
        amount: amtVal,
      },
    });
  };

  const amountVal = parseFloat(amount) || 0;
  const exceedsLimit = amountVal > remaining;

  return (
    <div className="min-h-screen grid lg:grid-cols-[260px_1fr] bg-slate-50 font-sans">
      {/* Sidebar for Desktop */}
      <div className="hidden lg:block">
        <Sidebar />
      </div>

      {/* Mobile Sidebar Overlay */}
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
          {/* Header */}
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate(-1)}
              className="w-10 h-10 bg-white border border-slate-200 rounded-full flex items-center justify-center hover:bg-slate-50 transition-colors shadow-sm cursor-pointer"
            >
              <ArrowLeft size={18} className="text-slate-600" />
            </button>
            <div>
              <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">Mobile Recharge</h1>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mt-0.5">Refill mobile airtime instantly</p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-[1fr_380px] gap-6 items-start">
            {/* Left Column: Form & Inputs */}
            <div className="space-y-6">
              <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-200">
                <form onSubmit={handleRecharge} className="space-y-6">
                  {/* Phone Number Input */}
                  <div>
                    <label className="block mb-2 text-slate-700 font-bold text-sm">Mobile Number</label>
                    <div className="relative">
                      <Smartphone className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                      <input
                        type="tel"
                        placeholder="e.g. 017XXXXXXXX"
                        maxLength={11}
                        value={mobileNumber}
                        onChange={(e) => setMobileNumber(e.target.value.replace(/\D/g, ''))}
                        className={`w-full pl-10 pr-4 py-3 bg-slate-50 rounded-xl border focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all font-medium text-slate-800 text-sm ${
                          showPhoneError ? 'border-red-500 focus:ring-red-500' : 'border-slate-200'
                        }`}
                      />
                    </div>
                    {showPhoneError && (
                      <p className="mt-1.5 text-xs font-bold text-red-600 flex items-center gap-1">
                        <AlertCircle size={14} />
                        Must be a valid 11-digit Bangladeshi number starting with 01
                      </p>
                    )}
                    {isPhoneValid && (
                      <p className="mt-1.5 text-xs font-bold text-emerald-600 flex items-center gap-1">
                        <CheckCircle size={14} />
                        Valid phone number structure
                      </p>
                    )}
                  </div>

                  {/* Select Operator Grid */}
                  <div>
                    <label className="block mb-3 text-slate-700 font-bold text-sm">Select Operator</label>
                    <div className="grid grid-cols-5 gap-2.5">
                      {operators.map((op) => (
                        <button
                          key={op.id}
                          type="button"
                          onClick={() => setSelectedOperator(op)}
                          className={`flex flex-col items-center justify-center p-3 rounded-2xl border transition-all duration-300 group cursor-pointer aspect-square ${
                            selectedOperator?.id === op.id
                              ? 'border-blue-600 bg-blue-50/50 shadow-sm ring-1 ring-blue-500'
                              : 'border-slate-200 hover:border-blue-600/30 hover:bg-slate-50/30'
                          }`}
                        >
                          <div className={`w-10 h-10 rounded-xl flex items-center justify-center font-black text-sm shrink-0 transition-transform duration-300 group-hover:scale-105 shadow-sm ${op.color} ${op.textColor}`}>
                            {op.logoInitial}
                          </div>
                          <span className="text-[10px] font-extrabold text-slate-500 group-hover:text-slate-800 transition-colors mt-2 text-center truncate w-full">
                            {op.name.split(' ')[0]}
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Amount Input */}
                  <div>
                    <Input
                      label="Amount (BDT)"
                      type="number"
                      placeholder="Enter amount (Min ৳10)"
                      value={amount}
                      onChange={(e) => setAmount(e.target.value)}
                      error={exceedsLimit ? 'Exceeds daily petty cash limit' : undefined}
                      required
                      min="10"
                      step="1"
                    />
                    <div className="mt-2 text-xs font-bold text-slate-400 flex items-center justify-between">
                      <span>Daily Limit Remaining:</span>
                      <span className="text-[#2563EB]">৳{remaining.toFixed(2)}</span>
                    </div>

                    {/* Presets Grid */}
                    <div className="grid grid-cols-5 gap-2 mt-4">
                      {presets.map((preset) => (
                        <button
                          key={preset}
                          type="button"
                          onClick={() => setAmount(preset.toString())}
                          className="py-2.5 bg-slate-50 hover:bg-blue-50 hover:text-blue-600 text-slate-600 border border-slate-200 hover:border-blue-300 rounded-xl text-xs font-extrabold transition-all duration-200 cursor-pointer active:scale-95 text-center"
                        >
                          ৳{preset}
                        </button>
                      ))}
                    </div>
                  </div>

                  {exceedsLimit && (
                    <div className="bg-red-50 border border-red-200 rounded-2xl p-4 flex items-start gap-3 animate-in fade-in duration-200">
                      <AlertCircle size={18} className="text-red-600 shrink-0 mt-0.5" />
                      <div>
                        <p className="text-sm font-bold text-red-900">Exceeds Daily Petty Cash Limit</p>
                        <p className="text-xs text-red-800 mt-1">
                          Maximum allowed transaction BDT {remaining.toFixed(2)}.
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Submit Button */}
                  <Button 
                    type="submit" 
                    fullWidth 
                    disabled={!isPhoneValid || !selectedOperator || !amount || parseFloat(amount) < 10 || exceedsLimit}
                  >
                    Continue to Recharge
                  </Button>
                </form>
              </div>
            </div>

            {/* Right Column: Recent Activity & Guidelines */}
            <div className="space-y-6">
              {/* Recent Recharge Payments */}
              <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-200">
                <h3 className="mb-4 text-slate-800 font-extrabold text-base tracking-tight">Recent Recharges</h3>
                {recentRecharges.length > 0 ? (
                  <div className="space-y-3">
                    {recentRecharges.map((txn, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-slate-50 border border-slate-100 rounded-2xl">
                        <div>
                          <p className="text-xs font-bold text-slate-800">Mobile Airtime Refill</p>
                          <p className="text-[10px] font-semibold text-slate-400">{new Date(txn.created_at).toLocaleDateString()}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-extrabold text-slate-800">৳{txn.amount.toFixed(2)}</p>
                          <p className="text-[10px] font-black text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-lg inline-block">Success</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="rounded-2xl border border-dashed border-slate-200 p-6 text-center">
                    <p className="text-xs font-medium text-slate-400">No recharges recorded yet</p>
                  </div>
                )}
              </div>

              {/* Info Card */}
              <div className="bg-blue-50/60 border border-blue-100 rounded-3xl p-6 space-y-4">
                <div className="flex items-center gap-2.5">
                  <Globe className="text-blue-600" size={20} />
                  <h4 className="text-sm font-extrabold text-blue-900 uppercase tracking-wider">Recharge Terms</h4>
                </div>
                <ul className="text-xs text-blue-800 font-semibold space-y-2.5">
                  <li className="flex gap-2">• <span>Min recharge amount is ৳10 BDT.</span></li>
                  <li className="flex gap-2">• <span>Recharge applies immediately to prepaid/postpaid connections.</span></li>
                  <li className="flex gap-2">• <span>Ensure you have selected the correct mobile carrier.</span></li>
                </ul>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
