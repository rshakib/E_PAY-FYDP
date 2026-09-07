import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import { Sidebar } from '../components/Sidebar';
import { Navbar } from '../components/Navbar';
import { Input } from '../components/Input';
import { Button } from '../components/Button';
import { 
  Search, ArrowLeft, Store, ChevronRight, Info, AlertCircle, 
  CheckCircle, Loader, ArrowUpRight 
} from 'lucide-react';
import { getUserSession } from '../../utils/session';
import { getTransactionHistory, checkReceiver } from '../../utils/api';

interface Merchant {
  id: string;
  name: string;
  category: string;
  username: string;
  avatarColor: string;
  initials: string;
}

export function MerchantPayment() {
  const navigate = useNavigate();
  const session = getUserSession();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchingMerchant, setSearchingMerchant] = useState(false);
  const [searchedMerchant, setSearchedMerchant] = useState<Merchant | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [selectedMerchant, setSelectedMerchant] = useState<Merchant | null>(null);
  const [amount, setAmount] = useState('');
  const [recentPayments, setRecentPayments] = useState<any[]>([]);

  useEffect(() => {
    if (!session) {
      navigate('/login');
      return;
    }

    async function loadRecentMerchantPayments() {
      try {
        const result = await getTransactionHistory(session!.username);
        if (result?.transactions) {
          // Filter transactions that went to merchant_store or are classified as merchant payments
          const merchantTxns = result.transactions.filter((tx: any) => 
            tx.status === 'success' && 
            tx.type === 'sent' && 
            tx.receiver_username === 'merchant_store'
          );
          setRecentPayments(merchantTxns.slice(0, 5));
        }
      } catch (err) {
        console.error('Error loading merchant transactions:', err);
      }
    }

    loadRecentMerchantPayments();
  }, [session?.username]);

  if (!session) {
    return null;
  }

  const dailyLimit = session.daily_limit;
  const spent = session.today_spent;
  const remaining = dailyLimit - spent;

  const recommendedMerchants: Merchant[] = [
    { id: '1', name: 'SuperMart Central', category: 'Grocery', username: 'supermart', avatarColor: 'bg-emerald-100 text-emerald-600', initials: 'SM' },
    { id: '2', name: 'Tech Haven', category: 'Electronics', username: 'techhaven', avatarColor: 'bg-blue-100 text-blue-600', initials: 'TH' },
  ];

  const recentMerchants: Merchant[] = [
    { id: 'rec-1', name: 'SuperMart Central', category: 'Grocery', username: 'supermart', avatarColor: 'bg-slate-100 text-slate-700', initials: 'SM' },
    { id: 'rec-2', name: 'Tech Haven', category: 'Electronics', username: 'techhaven', avatarColor: 'bg-slate-100 text-slate-700', initials: 'TH' },
    { id: 'rec-3', name: 'City Cafe', category: 'Food & Beverage', username: 'citycafe', avatarColor: 'bg-slate-100 text-slate-700', initials: 'CC' },
  ];

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim().length < 3) {
      setSearchError('Please enter at least 3 characters');
      return;
    }

    setSearchingMerchant(true);
    setSearchError(null);
    setSearchedMerchant(null);

    try {
      const result = await checkReceiver(searchQuery.trim());
      if (result.found) {
        const foundUsername = result.username || searchQuery.trim();
        const newMerchant: Merchant = {
          id: 'found',
          name: foundUsername === 'merchant_store' ? 'Niropay Merchant' : foundUsername,
          category: 'Verified Merchant',
          username: foundUsername,
          avatarColor: 'bg-blue-100 text-blue-600',
          initials: foundUsername.slice(0, 2).toUpperCase(),
        };
        setSearchedMerchant(newMerchant);
        setSelectedMerchant(newMerchant);
      } else {
        setSearchError('Merchant not found in database');
      }
    } catch (err) {
      console.error(err);
      setSearchError('Error searching merchant');
    } finally {
      setSearchingMerchant(false);
    }
  };

  const handlePay = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedMerchant) return;

    const amtVal = parseFloat(amount);
    if (isNaN(amtVal) || amtVal <= 0) {
      alert('Please enter a valid amount');
      return;
    }

    if (amtVal > remaining) {
      alert(`Amount exceeds daily petty cash limit. Remaining: ৳${remaining.toFixed(2)}`);
      return;
    }

    navigate('/transaction-processing', {
      state: {
        receiverUsername: selectedMerchant.username,
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
              <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">Merchant Payment</h1>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mt-0.5">Pay retail outlets & services</p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-[1fr_380px] gap-6 items-start">
            {/* Left Column: Selection & Payment Form */}
            <div className="space-y-6">
              {/* Search Merchant */}
              <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-200">
                <h3 className="mb-4 text-slate-800 font-extrabold text-base tracking-tight">Search Merchant</h3>
                <form onSubmit={handleSearch} className="flex gap-2">
                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                    <input
                      type="text"
                      placeholder="Enter merchant name or ID"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full pl-10 pr-4 py-3 bg-slate-50 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all font-medium text-slate-800 text-sm"
                    />
                  </div>
                  <Button type="submit" disabled={searchingMerchant} className="px-5 py-3 text-sm">
                    {searchingMerchant ? <Loader size={16} className="animate-spin" /> : 'Search'}
                  </Button>
                </form>
                {searchError && (
                  <p className="mt-2 text-xs font-bold text-red-600 flex items-center gap-1.5">
                    <AlertCircle size={14} />
                    {searchError}
                  </p>
                )}
                {searchedMerchant && (
                  <div className="mt-4 p-3 bg-blue-50/50 border border-blue-100 rounded-2xl flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center font-bold ${searchedMerchant.avatarColor}`}>
                        {searchedMerchant.initials}
                      </div>
                      <div>
                        <h4 className="text-sm font-bold text-slate-800">{searchedMerchant.name}</h4>
                        <p className="text-xs font-medium text-slate-400">@{searchedMerchant.username}</p>
                      </div>
                    </div>
                    <span className="text-xs font-extrabold text-blue-600 bg-blue-50 px-2.5 py-1 rounded-xl">Found</span>
                  </div>
                )}
              </div>

              {/* Recommended Merchants */}
              <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-200">
                <h3 className="mb-4 text-slate-800 font-extrabold text-base tracking-tight">Recommended Merchants</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                  {recommendedMerchants.map((merchant) => (
                    <button
                      key={merchant.id}
                      onClick={() => {
                        setSelectedMerchant(merchant);
                        setSearchedMerchant(null);
                      }}
                      className={`flex items-center gap-3.5 p-4 rounded-2xl border text-left transition-all duration-300 group cursor-pointer ${
                        selectedMerchant?.id === merchant.id
                          ? 'border-blue-600 bg-blue-50/40 shadow-sm'
                          : 'border-slate-200 hover:border-blue-600/30 hover:shadow-sm'
                      }`}
                    >
                      <div className={`w-12 h-12 rounded-2xl flex items-center justify-center font-bold text-lg transition-transform duration-300 group-hover:scale-105 shrink-0 ${merchant.avatarColor}`}>
                        {merchant.initials}
                      </div>
                      <div>
                        <h4 className="text-sm font-bold text-slate-800 leading-snug">{merchant.name}</h4>
                        <p className="text-xs font-medium text-slate-400 mt-0.5">{merchant.category}</p>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Payment Details Form */}
              {selectedMerchant && (
                <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-200 animate-in fade-in slide-in-from-bottom-2 duration-300">
                  <div className="flex items-center gap-3.5 pb-4 border-b border-slate-100 mb-6">
                    <div className={`w-12 h-12 rounded-2xl flex items-center justify-center font-bold text-lg shrink-0 ${selectedMerchant.avatarColor}`}>
                      {selectedMerchant.initials}
                    </div>
                    <div>
                      <span className="text-[10px] font-black uppercase tracking-wider text-blue-600">Paying Merchant</span>
                      <h3 className="text-slate-800 font-extrabold text-lg tracking-tight leading-snug">{selectedMerchant.name}</h3>
                      <p className="text-xs font-medium text-slate-400">@{selectedMerchant.username}</p>
                    </div>
                  </div>

                  <form onSubmit={handlePay} className="space-y-5">
                    <div>
                      <Input
                        label="Amount (BDT)"
                        type="number"
                        placeholder="0.00"
                        value={amount}
                        onChange={(e) => setAmount(e.target.value)}
                        error={exceedsLimit ? 'Exceeds daily petty cash limit' : undefined}
                        required
                        min="1"
                        step="0.01"
                      />
                      <div className="mt-2 text-xs font-bold text-slate-400 flex items-center justify-between">
                        <span>Daily Limit Remaining:</span>
                        <span className="text-[#2563EB]">৳{remaining.toFixed(2)}</span>
                      </div>
                    </div>

                    {exceedsLimit && (
                      <div className="bg-red-50 border border-red-200 rounded-2xl p-4 flex items-start gap-3">
                        <AlertCircle size={18} className="text-red-600 shrink-0 mt-0.5" />
                        <div>
                          <p className="text-sm font-bold text-red-900">Exceeds Daily Petty Cash Limit</p>
                          <p className="text-xs text-red-800 mt-1">
                            Maximum allowed transaction BDT {remaining.toFixed(2)}. Please try a lower amount.
                          </p>
                        </div>
                      </div>
                    )}

                    <Button type="submit" fullWidth disabled={exceedsLimit || !amount || parseFloat(amount) <= 0}>
                      Proceed to Pay
                    </Button>
                  </form>
                </div>
              )}
            </div>

            {/* Right Column: Recent Merchants & Info */}
            <div className="space-y-6">
              {/* Recent Merchants */}
              <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-200">
                <h3 className="mb-4 text-slate-800 font-extrabold text-base tracking-tight">Recent Merchants</h3>
                <div className="space-y-3">
                  {recentMerchants.map((merchant) => (
                    <button
                      key={merchant.id}
                      onClick={() => {
                        setSelectedMerchant(merchant);
                        setSearchedMerchant(null);
                      }}
                      className="w-full flex items-center justify-between p-3.5 rounded-2xl border border-slate-100 hover:border-blue-600/30 hover:bg-slate-50/50 transition-all duration-300 group cursor-pointer"
                    >
                      <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center font-bold text-sm shrink-0 ${merchant.avatarColor}`}>
                          {merchant.initials}
                        </div>
                        <div className="text-left">
                          <h4 className="text-sm font-bold text-slate-800 group-hover:text-blue-600 transition-colors leading-snug">{merchant.name}</h4>
                          <p className="text-xs font-semibold text-slate-400 leading-none mt-0.5">{merchant.category}</p>
                        </div>
                      </div>
                      <ChevronRight size={16} className="text-slate-400 group-hover:translate-x-0.5 transition-transform" />
                    </button>
                  ))}
                </div>
              </div>

              {/* Recent Merchant Payments Transactions History */}
              {recentPayments.length > 0 && (
                <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-200">
                  <h3 className="mb-4 text-slate-800 font-extrabold text-base tracking-tight">Recent Payments</h3>
                  <div className="space-y-3">
                    {recentPayments.map((txn, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-slate-50 border border-slate-100 rounded-2xl">
                        <div>
                          <p className="text-xs font-bold text-slate-800">Payment to Merchant</p>
                          <p className="text-[10px] font-semibold text-slate-400">{new Date(txn.created_at).toLocaleDateString()}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-extrabold text-slate-800">৳{txn.amount.toFixed(2)}</p>
                          <p className="text-[10px] font-black text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-lg inline-block">Success</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Security info card */}
              <div className="bg-blue-50/60 border border-blue-100 rounded-3xl p-6 space-y-4">
                <div className="flex items-center gap-2.5">
                  <Store className="text-blue-600" size={20} />
                  <h4 className="text-sm font-extrabold text-blue-900 uppercase tracking-wider">Merchant Info</h4>
                </div>
                <ul className="text-xs text-blue-800 font-semibold space-y-2.5">
                  <li className="flex gap-2">• <span>Verify merchant identity prior to payment.</span></li>
                  <li className="flex gap-2">• <span>Payments automatically verified through secure key rotation.</span></li>
                  <li className="flex gap-2">• <span>Maximum limit per transaction is bound by daily limits.</span></li>
                </ul>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
