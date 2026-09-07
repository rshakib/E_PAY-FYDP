import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import { Sidebar } from '../components/Sidebar';
import { Navbar } from '../components/Navbar';
import { Input } from '../components/Input';
import { Button } from '../components/Button';
import { 
  ArrowLeft, QrCode, Camera, Upload, Keyboard, ChevronRight, 
  Info, AlertCircle, CheckCircle, Store, Loader 
} from 'lucide-react';
import { getUserSession } from '../../utils/session';
import { getTransactionHistory } from '../../utils/api';

interface ScannedData {
  name: string;
  username: string;
  amount: number;
}

export function QRPay() {
  const navigate = useNavigate();
  const session = getUserSession();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  
  // Simulation states
  const [scanning, setScanning] = useState(false);
  const [scannedData, setScannedData] = useState<ScannedData | null>(null);
  
  // Manual Entry Form states
  const [showManualForm, setShowManualForm] = useState(false);
  const [manualUsername, setManualUsername] = useState('');
  const [manualAmount, setManualAmount] = useState('');

  const [recentQRPayments, setRecentQRPayments] = useState<any[]>([]);

  useEffect(() => {
    if (!session) {
      navigate('/login');
      return;
    }

    async function loadRecentQRPayments() {
      try {
        const result = await getTransactionHistory(session!.username);
        if (result?.transactions) {
          // Filter transactions that went to merchant_store (QR Pay targets merchants)
          const qrTxns = result.transactions.filter((tx: any) => 
            tx.status === 'success' && 
            tx.type === 'sent' && 
            tx.receiver_username === 'merchant_store'
          );
          setRecentQRPayments(qrTxns.slice(0, 3));
        }
      } catch (err) {
        console.error('Error loading QR transactions:', err);
      }
    }

    loadRecentQRPayments();
  }, [session?.username]);

  if (!session) {
    return null;
  }

  const dailyLimit = session.daily_limit;
  const spent = session.today_spent;
  const remaining = dailyLimit - spent;

  const handleSimulateScan = () => {
    setScanning(true);
    setScannedData(null);
    setShowManualForm(false);
    
    setTimeout(() => {
      setScanning(false);
      setScannedData({
        name: 'SuperMart Central',
        username: 'merchant_store',
        amount: 100.00
      });
    }, 1500);
  };

  const handleSimulateUpload = () => {
    setScanning(true);
    setScannedData(null);
    setShowManualForm(false);

    setTimeout(() => {
      setScanning(false);
      setScannedData({
        name: 'Tech Haven Outlet',
        username: 'merchant_store',
        amount: 150.00
      });
    }, 1200);
  };

  const handlePayScanned = () => {
    if (!scannedData) return;

    if (scannedData.amount > remaining) {
      alert(`Amount exceeds daily petty cash limit. Remaining: ৳${remaining.toFixed(2)}`);
      return;
    }

    navigate('/transaction-processing', {
      state: {
        receiverUsername: scannedData.username,
        amount: scannedData.amount
      }
    });
  };

  const handleManualSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const amtVal = parseFloat(manualAmount);

    if (isNaN(amtVal) || amtVal <= 0) {
      alert('Please enter a valid amount');
      return;
    }

    if (amtVal > remaining) {
      alert(`Amount exceeds daily petty cash limit. Remaining: ৳${remaining.toFixed(2)}`);
      return;
    }

    if (!manualUsername.trim()) {
      alert('Please enter a valid merchant code');
      return;
    }

    navigate('/transaction-processing', {
      state: {
        receiverUsername: manualUsername.trim(),
        amount: amtVal
      }
    });
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-[260px_1fr] bg-slate-50 font-sans">
      {/* Self-contained CSS scan line animation styles */}
      <style>{`
        @keyframes scan {
          0%, 100% { top: 0%; opacity: 0.8; }
          50% { top: 100%; opacity: 0.8; }
        }
        .scanner-line {
          animation: scan 2.5s linear infinite;
        }
      `}</style>

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
              <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">QR Pay</h1>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mt-0.5">Scan merchant codes & pay instantly</p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-[1fr_380px] gap-6 items-start">
            {/* Left Column: QR Viewfinder & Scan Confirmations */}
            <div className="space-y-6">
              
              {/* Scanner Frame Box */}
              <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-200 flex flex-col items-center justify-center text-center space-y-6">
                <h3 className="text-slate-800 font-extrabold text-base tracking-tight select-none">
                  Align QR Code within the frame
                </h3>

                {/* Viewfinder area */}
                <div className="w-64 h-64 bg-slate-900 rounded-3xl relative overflow-hidden flex items-center justify-center border-4 border-slate-800 shadow-inner">
                  {/* Corner styling corners decoration */}
                  <div className="absolute top-3 left-3 w-6 h-6 border-t-4 border-l-4 border-blue-500 rounded-tl-lg" />
                  <div className="absolute top-3 right-3 w-6 h-6 border-t-4 border-r-4 border-blue-500 rounded-tr-lg" />
                  <div className="absolute bottom-3 left-3 w-6 h-6 border-b-4 border-l-4 border-blue-500 rounded-bl-lg" />
                  <div className="absolute bottom-3 right-3 w-6 h-6 border-b-4 border-r-4 border-blue-500 rounded-br-lg" />

                  {/* Animated scan line */}
                  <div className="scanner-line absolute left-0 right-0 h-1 bg-gradient-to-r from-transparent via-blue-400 to-transparent shadow-[0_0_10px_#3b82f6]" />

                  {/* Camera placeholder drawing */}
                  <div className="text-slate-700 flex flex-col items-center space-y-2 select-none">
                    <Camera size={48} className="text-slate-600 animate-pulse" />
                    <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">
                      {scanning ? 'Initializing...' : 'Camera Standby'}
                    </span>
                  </div>
                </div>

                {/* Action Row */}
                <div className="w-full grid grid-cols-3 gap-2.5 max-w-md">
                  <button
                    onClick={handleSimulateScan}
                    className="flex flex-col items-center justify-center p-3 border border-slate-200 hover:border-blue-600 hover:bg-blue-50/50 rounded-2xl transition-all duration-300 group cursor-pointer"
                  >
                    <QrCode size={18} className="text-blue-600 group-hover:scale-105 transition-transform" />
                    <span className="text-[9px] font-bold text-slate-500 group-hover:text-slate-800 mt-2 text-center leading-tight">
                      Scan QR
                    </span>
                  </button>
                  <button
                    onClick={handleSimulateUpload}
                    className="flex flex-col items-center justify-center p-3 border border-slate-200 hover:border-blue-600 hover:bg-blue-50/50 rounded-2xl transition-all duration-300 group cursor-pointer"
                  >
                    <Upload size={18} className="text-blue-600 group-hover:scale-105 transition-transform" />
                    <span className="text-[9px] font-bold text-slate-500 group-hover:text-slate-800 mt-2 text-center leading-tight">
                      Upload QR
                    </span>
                  </button>
                  <button
                    onClick={() => {
                      setShowManualForm(!showManualForm);
                      setScannedData(null);
                    }}
                    className={`flex flex-col items-center justify-center p-3 border rounded-2xl transition-all duration-300 group cursor-pointer ${
                      showManualForm ? 'border-blue-600 bg-blue-50' : 'border-slate-200 hover:border-blue-600 hover:bg-blue-50/50'
                    }`}
                  >
                    <Keyboard size={18} className="text-blue-600 group-hover:scale-105 transition-transform" />
                    <span className="text-[9px] font-bold text-slate-500 group-hover:text-slate-800 mt-2 text-center leading-tight">
                      Enter Code
                    </span>
                  </button>
                </div>
              </div>

              {/* Scanned Confirm Modal Card */}
              {scannedData && (
                <div className="bg-white rounded-3xl p-6 shadow-sm border border-blue-200 animate-in fade-in slide-in-from-bottom-2 duration-300">
                  <div className="flex items-center gap-3.5 pb-4 border-b border-slate-100 mb-6">
                    <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
                      <Store size={22} />
                    </div>
                    <div>
                      <span className="text-[10px] font-black uppercase tracking-wider text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-lg border border-emerald-100">
                        Scan Success
                      </span>
                      <h3 className="text-slate-800 font-extrabold text-lg tracking-tight leading-snug mt-1.5">{scannedData.name}</h3>
                      <p className="text-xs font-semibold text-slate-400">@{scannedData.username}</p>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="flex justify-between items-center bg-slate-50 p-4 border border-slate-100 rounded-2xl">
                      <span className="text-xs font-bold text-slate-500 uppercase">Payment Amount:</span>
                      <span className="text-lg font-black text-slate-800">৳{scannedData.amount.toFixed(2)}</span>
                    </div>

                    <div className="text-xs font-bold text-slate-400 flex items-center justify-between px-1">
                      <span>Daily Limit Remaining:</span>
                      <span className="text-[#2563EB]">৳{remaining.toFixed(2)}</span>
                    </div>

                    <Button onClick={handlePayScanned} fullWidth disabled={scannedData.amount > remaining}>
                      Confirm & Pay
                    </Button>
                  </div>
                </div>
              )}

              {/* Manual Entry Form */}
              {showManualForm && (
                <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-200 animate-in fade-in slide-in-from-bottom-2 duration-300">
                  <h3 className="mb-4 text-slate-800 font-extrabold text-base tracking-tight pb-3 border-b border-slate-100">
                    Enter Merchant Code
                  </h3>
                  <form onSubmit={handleManualSubmit} className="space-y-4">
                    <Input
                      label="Merchant Account ID"
                      type="text"
                      placeholder="e.g. merchant_store"
                      value={manualUsername}
                      onChange={(e) => setManualUsername(e.target.value)}
                      required
                    />
                    <Input
                      label="Amount (BDT)"
                      type="number"
                      placeholder="0.00"
                      value={manualAmount}
                      onChange={(e) => setManualAmount(e.target.value)}
                      required
                      min="1"
                    />

                    <div className="text-xs font-bold text-slate-400 flex items-center justify-between px-1">
                      <span>Daily Limit Remaining:</span>
                      <span className="text-[#2563EB]">৳{remaining.toFixed(2)}</span>
                    </div>

                    <Button type="submit" fullWidth>
                      Proceed to Pay
                    </Button>
                  </form>
                </div>
              )}
            </div>

            {/* Right Column: Recent QR payments & info card */}
            <div className="space-y-6">
              {/* Recent QR Payments list */}
              <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-200">
                <h3 className="mb-4 text-slate-800 font-extrabold text-base tracking-tight">Recent QR Payments</h3>
                {recentQRPayments.length > 0 ? (
                  <div className="space-y-3">
                    {recentQRPayments.map((txn, index) => (
                      <div key={index} className="flex items-center justify-between p-3.5 bg-slate-50 border border-slate-100 rounded-2xl">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center text-blue-600 shadow-sm border border-slate-100 shrink-0">
                            <Store size={16} />
                          </div>
                          <div>
                            <h4 className="text-xs font-bold text-slate-800 leading-snug">Merchant Outlet</h4>
                            <p className="text-[10px] font-semibold text-slate-400 mt-0.5">{new Date(txn.created_at).toLocaleDateString()}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-black text-slate-800">৳{txn.amount.toFixed(2)}</p>
                          <span className="text-[9px] font-black text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded-lg inline-block">
                            SUCCESS
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="rounded-2xl border border-dashed border-slate-200 p-6 text-center">
                    <p className="text-xs font-medium text-slate-400">No QR transactions yet</p>
                  </div>
                )}
              </div>

              {/* Guide Card */}
              <div className="bg-blue-50/60 border border-blue-100 rounded-3xl p-6 space-y-4">
                <div className="flex items-center gap-2.5">
                  <Info className="text-blue-600" size={20} />
                  <h4 className="text-sm font-extrabold text-blue-900 uppercase tracking-wider">Quick Guide</h4>
                </div>
                <ul className="text-xs text-blue-800 font-semibold space-y-2.5">
                  <li className="flex gap-2">• <span>Re-position scanner if scan fails automatically.</span></li>
                  <li className="flex gap-2">• <span>QR Pay operates on verified merchant databases.</span></li>
                  <li className="flex gap-2">• <span>Limits and limits reset conform to daily constraints.</span></li>
                </ul>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
