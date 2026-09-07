import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import { TransactionCard } from '../components/TransactionCard';
import { Sidebar } from '../components/Sidebar';
import { Navbar } from '../components/Navbar';
import { ArrowLeft, Filter, Download, Info } from 'lucide-react';
import { getUserSession } from '../../utils/session';
import { getTransactionHistory } from '../../utils/api';

interface Transaction {
  id: string;
  amount: number;
  status: 'success' | 'rejected' | 'pending' | 'aborted' | 'futile';
  created_at: string;
  reference: string;
  type: 'sent' | 'received';
  senderUsername?: string;
  receiverUsername?: string;
  sender_username?: string;
  receiver_username?: string;
}

export function TransactionHistory() {
  const navigate = useNavigate();
  const session = getUserSession();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'all' | 'successful' | 'rejected'>('all');
  const [allTransactions, setAllTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!session) {
      console.error('User session not found');
      navigate('/login');
      setLoading(false);
      return;
    }

    const fetchTransactions = async () => {
      try {
        const data = await getTransactionHistory(session.username);

        if (data.status === 'success' && data.transactions) {
          setAllTransactions(data.transactions);
        }
      } catch (error) {
        console.error('Error fetching transactions:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTransactions();
  }, [session?.username, navigate]);

  const filteredTransactions = allTransactions.filter((transaction) => {
    if (activeTab === 'all') return true;
    if (activeTab === 'successful') return transaction.status === 'success';
    if (activeTab === 'rejected') {
      return transaction.status === 'rejected' || transaction.status === 'aborted' || transaction.status === 'futile';
    }
    return true;
  });

  const handleExportCSV = () => {
    if (allTransactions.length === 0) {
      alert('No transactions available to export.');
      return;
    }

    const headers = ['Transaction ID', 'Type', 'Sender', 'Receiver', 'Amount (BDT)', 'Date', 'Status', 'Reference'];
    const rows = allTransactions.map(tx => [
      tx.id,
      tx.type,
      tx.sender_username || tx.senderUsername || 'N/A',
      tx.receiver_username || tx.receiverUsername || 'N/A',
      tx.amount,
      new Date(tx.created_at).toLocaleString(),
      tx.status,
      tx.reference
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' 
      + [headers.join(','), ...rows.map(e => e.map(val => `"${val}"`).join(','))].join('\n');
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `niropay_ledger_${session?.username || 'user'}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const tabs = [
    { id: 'all' as const, label: 'All', count: allTransactions.length },
    { id: 'successful' as const, label: 'Successful', count: allTransactions.filter(t => t.status === 'success').length },
    { id: 'rejected' as const, label: 'Failed', count: allTransactions.filter(t => t.status !== 'success' && t.status !== 'pending').length },
  ];

  return (
    <div className="min-h-screen grid lg:grid-cols-[260px_1fr] bg-slate-50 font-sans">
      {/* Sidebar for Desktop */}
      <div className="hidden lg:block">
        <Sidebar />
      </div>

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex flex-row">
          <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm" onClick={() => setSidebarOpen(false)} />
          <div className="relative z-50 animate-in slide-in-from-left duration-200">
            <Sidebar />
          </div>
        </div>
      )}

      {/* Main Workspace */}
      <div className="flex flex-col min-h-screen overflow-x-hidden">
        <Navbar onMenuToggle={() => setSidebarOpen(true)} />

        <main className="flex-1 p-6 space-y-6 max-w-4xl w-full mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate(-1)}
                className="w-10 h-10 bg-white border border-slate-200 rounded-full flex items-center justify-center hover:bg-slate-50 transition-colors shadow-sm cursor-pointer"
              >
                <ArrowLeft size={18} className="text-slate-600" />
              </button>
              <div>
                <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">Transaction History</h1>
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mt-0.5">Review and export ledger transactions</p>
              </div>
            </div>

            <button
              onClick={handleExportCSV}
              className="flex items-center gap-2 px-4 py-2.5 bg-white border border-slate-200 hover:border-blue-600 hover:text-blue-600 text-slate-600 text-xs font-extrabold rounded-2xl transition-colors cursor-pointer shadow-sm active:scale-95"
            >
              <Download size={14} />
              Export CSV
            </button>
          </div>

          <div className="bg-white rounded-3xl shadow-sm border border-slate-200 overflow-hidden">
            {/* Filter Tabs */}
            <div className="border-b border-slate-100">
              <div className="flex">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex-1 px-4 py-4 text-xs font-extrabold uppercase tracking-wider transition-colors relative cursor-pointer ${
                      activeTab === tab.id
                        ? 'text-[#2563EB]'
                        : 'text-slate-400 hover:text-slate-600'
                    }`}
                  >
                    {tab.label}
                    <span className={`ml-2 px-2 py-0.5 rounded-lg text-[10px] font-black ${
                      activeTab === tab.id
                        ? 'bg-blue-100 text-[#2563EB]'
                        : 'bg-slate-100 text-slate-400'
                    }`}>
                      {tab.count}
                    </span>
                    {activeTab === tab.id && (
                      <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#2563EB] rounded-full" />
                    )}
                  </button>
                ))}
              </div>
            </div>

            <div className="p-6">
              {loading ? (
                <div className="text-center py-12">
                  <p className="text-xs font-semibold text-slate-400">Loading transaction history...</p>
                </div>
              ) : filteredTransactions.length > 0 ? (
                <div className="space-y-3">
                  {filteredTransactions.map((transaction) => (
                    <TransactionCard
                      key={transaction.id}
                      type={transaction.type}
                      amount={transaction.amount}
                      status={transaction.status}
                      timestamp={new Date(transaction.created_at).toLocaleString()}
                      senderUsername={transaction.sender_username || transaction.senderUsername}
                      receiverUsername={transaction.receiver_username || transaction.receiverUsername}
                    />
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 flex flex-col items-center justify-center">
                  <Filter size={44} className="text-slate-300 mb-3" />
                  <p className="text-xs font-bold text-slate-400">No transactions recorded in this category</p>
                </div>
              )}
            </div>
          </div>

          {/* Secure Audit Info */}
          <div className="bg-blue-50/60 border border-blue-100 rounded-3xl p-6 space-y-3">
            <div className="flex items-center gap-2.5">
              <Info className="text-blue-600" size={20} />
              <h4 className="text-sm font-extrabold text-blue-900 uppercase tracking-wider">Security Information</h4>
            </div>
            <p className="text-xs text-blue-800 font-semibold leading-relaxed">
              All successful transfers undergo strict cryptographic verification. Balance rotations and HMAC message 
              integrity checks protect transactions from tampering or replay events.
            </p>
          </div>
        </main>
      </div>
    </div>
  );
}
