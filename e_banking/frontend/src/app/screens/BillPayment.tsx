import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import { Sidebar } from '../components/Sidebar';
import { Navbar } from '../components/Navbar';
import { Button } from '../components/Button';
import { 
  ArrowLeft, Zap, Droplet, Flame, Wifi, Tv, Shield, 
  ChevronRight, Info, AlertCircle, CheckCircle, Receipt, ClipboardList 
} from 'lucide-react';
import { getUserSession } from '../../utils/session';
import { getTransactionHistory } from '../../utils/api';

interface Bill {
  id: string;
  name: string;
  category: string;
  provider: string;
  amount: number;
  receiver: string;
  dueDate: string;
  icon: any;
  iconBg: string;
  iconColor: string;
}

export function BillPayment() {
  const navigate = useNavigate();
  const session = getUserSession();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'unpaid' | 'paid'>('unpaid');
  const [unpaidBills, setUnpaidBills] = useState<Bill[]>([]);
  const [paidBills, setPaidBills] = useState<Bill[]>([]);
  const [loading, setLoading] = useState(true);

  const initialBillsList: Bill[] = [
    { 
      id: 'elec-desco', 
      name: 'DESCO Electricity', 
      category: 'Electricity', 
      provider: 'DESCO', 
      amount: 850.00, 
      receiver: 'desco', 
      dueDate: '2026-06-25', 
      icon: Zap, 
      iconBg: 'bg-amber-50', 
      iconColor: 'text-amber-500' 
    },
    { 
      id: 'water-wasa', 
      name: 'Dhaka WASA Water', 
      category: 'Water', 
      provider: 'WASA', 
      amount: 450.00, 
      receiver: 'wasa', 
      dueDate: '2026-06-28', 
      icon: Droplet, 
      iconBg: 'bg-blue-50', 
      iconColor: 'text-blue-500' 
    },
    { 
      id: 'gas-titas', 
      name: 'Titas Gas Bill', 
      category: 'Gas', 
      provider: 'Titas', 
      amount: 650.00, 
      receiver: 'gas_service', 
      dueDate: '2026-06-30', 
      icon: Flame, 
      iconBg: 'bg-orange-50', 
      iconColor: 'text-orange-500' 
    },
  ];

  const categories = [
    { icon: Zap, label: 'Electricity', bg: 'bg-amber-50 text-amber-600 border-amber-100 hover:border-amber-200' },
    { icon: Droplet, label: 'Water', bg: 'bg-blue-50 text-blue-600 border-blue-100 hover:border-blue-200' },
    { icon: Flame, label: 'Gas', bg: 'bg-orange-50 text-orange-600 border-orange-100 hover:border-orange-200' },
    { icon: Wifi, label: 'Internet', bg: 'bg-indigo-50 text-indigo-600 border-indigo-100 hover:border-indigo-200' },
    { icon: Tv, label: 'Television', bg: 'bg-purple-50 text-purple-600 border-purple-100 hover:border-purple-200' },
    { icon: Shield, label: 'Insurance', bg: 'bg-slate-50 text-slate-700 border-slate-200 hover:border-slate-300' },
  ];

  useEffect(() => {
    if (!session) {
      navigate('/login');
      return;
    }

    async function syncBillsWithHistory() {
      try {
        setLoading(true);
        const result = await getTransactionHistory(session!.username);
        
        if (result?.transactions) {
          const unpaidList: Bill[] = [];
          const paidList: Bill[] = [];

          initialBillsList.forEach(bill => {
            // Check if there is a successful transfer in the history that matches the biller username and amount
            const matchingTxn = result.transactions.find((tx: any) => 
              tx.status === 'success' && 
              tx.type === 'sent' && 
              tx.receiver_username === bill.receiver && 
              Math.abs(tx.amount - bill.amount) < 0.01
            );

            if (matchingTxn) {
              paidList.push(bill);
            } else {
              unpaidList.push(bill);
            }
          });

          setUnpaidBills(unpaidList);
          setPaidBills(paidList);
        } else {
          setUnpaidBills(initialBillsList);
          setPaidBills([]);
        }
      } catch (err) {
        console.error('Error syncing bill payments:', err);
        setUnpaidBills(initialBillsList);
      } finally {
        setLoading(false);
      }
    }

    syncBillsWithHistory();
  }, [session?.username]);

  if (!session) {
    return null;
  }

  const dailyLimit = session.daily_limit;
  const spent = session.today_spent;
  const remaining = dailyLimit - spent;

  const handlePayBill = (bill: Bill) => {
    if (bill.amount > remaining) {
      alert(`Amount exceeds daily petty cash limit. Remaining: ৳${remaining.toFixed(2)}`);
      return;
    }

    navigate('/transaction-processing', {
      state: {
        receiverUsername: bill.receiver,
        amount: bill.amount,
      },
    });
  };

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
              <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">Bill Payment</h1>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mt-0.5">Pay utilities & household bills</p>
            </div>
          </div>

          {/* Categories Grid */}
          <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-200">
            <h3 className="mb-4 text-slate-800 font-extrabold text-base tracking-tight">Bill Categories</h3>
            <div className="grid grid-cols-2 sm:grid-cols-6 gap-3.5">
              {categories.map((cat, idx) => {
                const Icon = cat.icon;
                return (
                  <div 
                    key={idx}
                    className="flex flex-col items-center justify-center p-4 rounded-2xl border border-slate-100 hover:shadow-sm hover:border-blue-600/30 transition-all duration-300 group cursor-pointer"
                  >
                    <div className={`w-11 h-11 rounded-2xl flex items-center justify-center shrink-0 shadow-sm transition-transform duration-300 group-hover:scale-105 ${cat.bg}`}>
                      <Icon size={20} />
                    </div>
                    <span className="text-[11px] font-bold text-slate-600 group-hover:text-slate-800 mt-2.5 text-center leading-tight">
                      {cat.label}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-[1fr_380px] gap-6 items-start">
            {/* Left Column: Unpaid and Paid Bills list */}
            <div className="space-y-6 bg-white rounded-3xl p-6 shadow-sm border border-slate-200">
              {/* Tab Selector */}
              <div className="flex border-b border-slate-100 pb-2 gap-4">
                <button
                  onClick={() => setActiveTab('unpaid')}
                  className={`pb-2 text-sm font-extrabold tracking-tight relative cursor-pointer ${
                    activeTab === 'unpaid' 
                      ? 'text-blue-600' 
                      : 'text-slate-400 hover:text-slate-600'
                  }`}
                >
                  Pending Bills
                  {unpaidBills.length > 0 && (
                    <span className="ml-1.5 px-1.5 py-0.5 bg-blue-100 text-blue-700 text-[10px] font-black rounded-lg">
                      {unpaidBills.length}
                    </span>
                  )}
                  {activeTab === 'unpaid' && (
                    <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600 rounded-full" />
                  )}
                </button>
                <button
                  onClick={() => setActiveTab('paid')}
                  className={`pb-2 text-sm font-extrabold tracking-tight relative cursor-pointer ${
                    activeTab === 'paid' 
                      ? 'text-blue-600' 
                      : 'text-slate-400 hover:text-slate-600'
                  }`}
                >
                  Payment History
                  {paidBills.length > 0 && (
                    <span className="ml-1.5 px-1.5 py-0.5 bg-emerald-100 text-emerald-700 text-[10px] font-black rounded-lg">
                      {paidBills.length}
                    </span>
                  )}
                  {activeTab === 'paid' && (
                    <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600 rounded-full" />
                  )}
                </button>
              </div>

              {loading ? (
                <div className="py-12 text-center text-slate-400 font-semibold text-xs">
                  Loading outstanding invoices...
                </div>
              ) : activeTab === 'unpaid' ? (
                unpaidBills.length > 0 ? (
                  <div className="divide-y divide-slate-100">
                    {unpaidBills.map((bill) => {
                      const Icon = bill.icon;
                      const exceeds = bill.amount > remaining;
                      return (
                        <div key={bill.id} className="flex flex-col sm:flex-row sm:items-center justify-between py-4 first:pt-0 last:pb-0 gap-4">
                          <div className="flex items-center gap-3.5">
                            <div className={`w-11 h-11 rounded-2xl flex items-center justify-center shrink-0 ${bill.iconBg} ${bill.iconColor}`}>
                              <Icon size={20} />
                            </div>
                            <div>
                              <h4 className="text-sm font-extrabold text-slate-800">{bill.name}</h4>
                              <p className="text-xs font-semibold text-slate-400 mt-0.5">Due: {bill.dueDate}</p>
                            </div>
                          </div>

                          <div className="flex items-center justify-between sm:justify-end gap-4">
                            <div className="text-right sm:mr-2">
                              <p className="text-sm font-black text-slate-800">৳{bill.amount.toFixed(2)}</p>
                              <p className="text-[10px] font-semibold text-[#2563EB]">PETTY CASH LIMIT</p>
                            </div>
                            <Button
                              variant={exceeds ? 'secondary' : 'primary'}
                              disabled={exceeds}
                              onClick={() => handlePayBill(bill)}
                              className="px-4 py-2 text-xs font-extrabold"
                            >
                              {exceeds ? 'Limit Exceeded' : 'Pay Now'}
                            </Button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="py-12 flex flex-col items-center justify-center text-center animate-in fade-in duration-300">
                    <div className="w-16 h-16 bg-emerald-50 text-emerald-500 rounded-full flex items-center justify-center mb-4 border border-emerald-100">
                      <CheckCircle size={32} />
                    </div>
                    <h4 className="text-slate-800 font-extrabold text-base tracking-tight">You're all caught up!</h4>
                    <p className="text-xs font-semibold text-slate-400 mt-1 max-w-[280px]">
                      No pending utility statements or outstanding dues found.
                    </p>
                  </div>
                )
              ) : paidBills.length > 0 ? (
                <div className="divide-y divide-slate-100">
                  {paidBills.map((bill) => {
                    const Icon = bill.icon;
                    return (
                      <div key={bill.id} className="flex items-center justify-between py-4 first:pt-0 last:pb-0 gap-4">
                        <div className="flex items-center gap-3.5">
                          <div className={`w-11 h-11 rounded-2xl flex items-center justify-center shrink-0 ${bill.iconBg} ${bill.iconColor}`}>
                            <Icon size={20} />
                          </div>
                          <div>
                            <h4 className="text-sm font-extrabold text-slate-800">{bill.name}</h4>
                            <p className="text-xs font-semibold text-slate-400 mt-0.5">Paid Successfully</p>
                          </div>
                        </div>

                        <div className="flex items-center gap-4">
                          <div className="text-right">
                            <p className="text-sm font-black text-slate-800">৳{bill.amount.toFixed(2)}</p>
                            <span className="text-[10px] font-black text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-lg inline-block mt-0.5">
                              PAID
                            </span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="py-12 text-center text-slate-400 font-semibold text-xs">
                  No payment statements found in transaction history.
                </div>
              )}
            </div>

            {/* Right Column: Limits and Information */}
            <div className="space-y-6">
              {/* Daily Limit status */}
              <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-200">
                <h3 className="mb-4 text-slate-800 font-extrabold text-base tracking-tight">Daily Spending Limit</h3>
                <div className="space-y-3">
                  <div className="flex justify-between text-xs font-bold text-slate-600">
                    <span>Today's Spending:</span>
                    <span>৳{spent.toFixed(2)} / ৳{dailyLimit.toFixed(2)}</span>
                  </div>
                  {/* Progress Bar */}
                  <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                    <div 
                      className="bg-blue-600 h-full transition-all duration-500"
                      style={{ width: `${Math.min((spent / dailyLimit) * 100, 100)}%` }}
                    />
                  </div>
                  <div className="text-[10px] font-semibold text-slate-400 flex items-center gap-1.5 pt-1">
                    <Info size={12} className="text-blue-500" />
                    <span>Petty cash limit resets daily at midnight.</span>
                  </div>
                </div>
              </div>

              {/* Guidelines info card */}
              <div className="bg-blue-50/60 border border-blue-100 rounded-3xl p-6 space-y-4">
                <div className="flex items-center gap-2.5">
                  <ClipboardList className="text-blue-600" size={20} />
                  <h4 className="text-sm font-extrabold text-blue-900 uppercase tracking-wider">Payment Guide</h4>
                </div>
                <ul className="text-xs text-blue-800 font-semibold space-y-2.5">
                  <li className="flex gap-2">• <span>Utility bills take up to 24 hours to clear on supplier databases.</span></li>
                  <li className="flex gap-2">• <span>Save statements to download digital receipts post confirmation.</span></li>
                  <li className="flex gap-2">• <span>No hidden service charge applied to standard bills.</span></li>
                </ul>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
