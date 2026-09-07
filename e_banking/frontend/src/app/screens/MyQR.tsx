import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import { Sidebar } from '../components/Sidebar';
import { Navbar } from '../components/Navbar';
import { Button } from '../components/Button';
import { 
  ArrowLeft, QrCode, Copy, Download, Share2, CheckCircle, 
  Info, User, ShieldCheck, CreditCard 
} from 'lucide-react';
import { getUserSession } from '../../utils/session';

export function MyQR() {
  const navigate = useNavigate();
  const session = getUserSession();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!session) {
      navigate('/login');
    }
  }, [session]);

  if (!session) {
    return null;
  }

  const username = session.username;
  const fullName = username === 'tester1' ? 'Tester One' : username === 'tester2' ? 'Tester Two' : username.charAt(0).toUpperCase() + username.slice(1);
  const paymentId = session.accountId || `ACC-${username.toUpperCase()}-9821`;

  const handleCopyId = () => {
    navigator.clipboard.writeText(paymentId);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSimulateAction = (action: string) => {
    alert(`${action} QR Code action simulated successfully (UI-only).`);
  };

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

      {/* Main Content Workspace */}
      <div className="flex flex-col min-h-screen overflow-x-hidden">
        <Navbar onMenuToggle={() => setSidebarOpen(true)} />

        <main className="flex-1 p-6 space-y-6 max-w-4xl w-full mx-auto">
          {/* Header */}
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate(-1)}
              className="w-10 h-10 bg-white border border-slate-200 rounded-full flex items-center justify-center hover:bg-slate-50 transition-colors shadow-sm cursor-pointer"
            >
              <ArrowLeft size={18} className="text-slate-600" />
            </button>
            <div>
              <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">My QR Code</h1>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mt-0.5">Show QR to receive transfers instantly</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-[1fr_360px] gap-6 items-start">
            
            {/* Left Column: Large QR Card & Actions */}
            <div className="bg-white rounded-3xl p-8 shadow-sm border border-slate-200 flex flex-col items-center justify-center text-center space-y-6">
              
              {/* Profile details header */}
              <div className="flex flex-col items-center space-y-3">
                <div className="w-16 h-16 rounded-2xl bg-blue-100 flex items-center justify-center text-blue-600 text-lg font-black shadow-inner select-none">
                  {username.slice(0, 2).toUpperCase()}
                </div>
                <div>
                  <div className="flex items-center justify-center gap-1.5">
                    <h2 className="text-lg font-black text-slate-800 tracking-tight">{fullName}</h2>
                    <ShieldCheck size={16} className="text-blue-600 shrink-0" />
                  </div>
                  <p className="text-xs font-semibold text-slate-400">@{username}</p>
                </div>
              </div>

              {/* QR Code Container */}
              <div className="p-6 bg-[#EFF6FF] border border-blue-100 rounded-3xl relative">
                {/* SVG Mock QR Code with three eye finder boxes and custom patterns */}
                <svg className="w-48 h-48 text-blue-900" viewBox="0 0 100 100" fill="currentColor">
                  {/* Background */}
                  <rect width="100" height="100" fill="#EFF6FF" />
                  
                  {/* Top-Left Eye Finder */}
                  <rect x="5" y="5" width="22" height="22" rx="3" fill="#1e3a8a" />
                  <rect x="9" y="9" width="14" height="14" rx="2" fill="#EFF6FF" />
                  <rect x="12" y="12" width="8" height="8" rx="1" fill="#1e3a8a" />
                  
                  {/* Top-Right Eye Finder */}
                  <rect x="73" y="5" width="22" height="22" rx="3" fill="#1e3a8a" />
                  <rect x="77" y="9" width="14" height="14" rx="2" fill="#EFF6FF" />
                  <rect x="80" y="12" width="8" height="8" rx="1" fill="#1e3a8a" />
                  
                  {/* Bottom-Left Eye Finder */}
                  <rect x="5" y="73" width="22" height="22" rx="3" fill="#1e3a8a" />
                  <rect x="9" y="77" width="14" height="14" rx="2" fill="#EFF6FF" />
                  <rect x="12" y="80" width="8" height="8" rx="1" fill="#1e3a8a" />

                  {/* QR Pattern dots simulated using high fidelity grid pixels path */}
                  <path d="
                    M 35,5 h 5 v 5 h -5 z M 45,5 h 10 v 5 h -10 z M 60,5 h 5 v 10 h -5 z 
                    M 35,15 h 15 v 5 h -15 z M 55,15 h 5 v 5 h -5 z M 65,15 h 5 v 5 h -5 z
                    M 35,25 h 5 v 10 h -5 z M 45,25 h 5 v 5 h -5 z M 55,25 h 15 v 5 h -15 z
                    M 5,35 h 15 v 5 h -15 z M 25,35 h 10 v 5 h -10 z M 45,35 h 5 v 5 h -5 z M 55,35 h 5 v 5 h -5 z M 65,35 h 10 v 5 h -10 z
                    M 5,45 h 5 v 10 h -5 z M 15,45 h 10 v 5 h -10 z M 30,45 h 10 v 5 h -10 z M 45,45 h 15 v 5 h -15 z M 65,45 h 5 v 10 h -5 z
                    M 5,60 h 10 v 5 h -10 z M 20,60 h 5 v 5 h -5 z M 30,60 h 15 v 5 h -15 z M 50,60 h 10 v 5 h -10 z M 65,60 h 15 v 5 h -15 z
                    M 35,70 h 5 v 5 h -5 z M 45,70 h 10 v 5 h -10 z M 60,70 h 5 v 5 h -5 z M 70,70 h 5 v 5 h -5 z
                    M 35,80 h 15 v 5 h -15 z M 55,80 h 5 v 5 h -5 z M 65,80 h 20 v 5 h -20 z
                    M 35,90 h 5 v 5 h -5 z M 45,90 h 5 v 5 h -5 z M 55,90 h 15 v 5 h -15 z M 75,90 h 10 v 5 h -10 z
                  " fill="#1e40af" />
                  
                  {/* Central Overlay Box containing initials */}
                  <rect x="40" y="40" width="20" height="20" rx="4" fill="#ffffff" stroke="#EFF6FF" strokeWidth="2" />
                  <text x="50" y="53" textAnchor="middle" fontSize="10" fontWeight="900" fill="#2563EB" fontFamily="sans-serif">
                    NP
                  </text>
                </svg>
              </div>

              {/* QR Actions */}
              <div className="w-full grid grid-cols-2 gap-3 max-w-sm">
                <button
                  onClick={() => handleSimulateAction('Download')}
                  className="flex items-center justify-center gap-2 py-3 border border-slate-200 hover:border-blue-600 hover:bg-blue-50/50 rounded-2xl text-xs font-extrabold text-slate-600 hover:text-blue-600 transition-colors cursor-pointer"
                >
                  <Download size={15} />
                  Download QR
                </button>
                <button
                  onClick={() => handleSimulateAction('Share')}
                  className="flex items-center justify-center gap-2 py-3 border border-slate-200 hover:border-blue-600 hover:bg-blue-50/50 rounded-2xl text-xs font-extrabold text-slate-600 hover:text-blue-600 transition-colors cursor-pointer"
                >
                  <Share2 size={15} />
                  Share QR
                </button>
              </div>
            </div>

            {/* Right Column: Payment Info & Usage Guide */}
            <div className="space-y-6">
              
              {/* Payment Information */}
              <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-200 space-y-4">
                <h3 className="text-slate-800 font-extrabold text-base tracking-tight pb-3 border-b border-slate-100 flex items-center gap-2">
                  <CreditCard size={18} className="text-blue-600" />
                  Payment Details
                </h3>

                <div className="space-y-3.5">
                  <div>
                    <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest block mb-1">
                      Wallet Username
                    </span>
                    <span className="text-sm font-bold text-slate-700">@{username}</span>
                  </div>

                  <div className="border-t border-slate-50 pt-3">
                    <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest block mb-1">
                      Account Type
                    </span>
                    <span className="text-sm font-bold text-slate-700">Personal Account</span>
                  </div>

                  <div className="border-t border-slate-50 pt-3">
                    <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest block mb-1">
                      Payment ID / Account Number
                    </span>
                    <div className="flex items-center justify-between gap-3 bg-slate-50 p-3 rounded-2xl border border-slate-150 font-mono text-xs text-slate-700">
                      <span className="truncate">{paymentId}</span>
                      <button
                        onClick={handleCopyId}
                        className="p-1 hover:bg-slate-200 text-slate-500 hover:text-slate-800 rounded-lg transition-colors cursor-pointer shrink-0"
                        title="Copy Account ID"
                      >
                        {copied ? <CheckCircle size={15} className="text-emerald-600" /> : <Copy size={15} />}
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Usage Guide */}
              <div className="bg-blue-50/60 border border-blue-100 rounded-3xl p-6 space-y-4">
                <div className="flex items-center gap-2.5">
                  <Info className="text-blue-600" size={20} />
                  <h4 className="text-sm font-extrabold text-blue-900 uppercase tracking-wider">How to use</h4>
                </div>
                <ul className="text-xs text-blue-800 font-semibold space-y-2.5">
                  <li className="flex gap-2">
                    <span>•</span>
                    <span>Let other Niropay users scan this QR code using their QR Pay viewfinder to send you funds instantly.</span>
                  </li>
                  <li className="flex gap-2">
                    <span>•</span>
                    <span>Received payments are credited immediately to your bank-backed account balance ledger.</span>
                  </li>
                  <li className="flex gap-2">
                    <span>•</span>
                    <span>All transactions are fully secured using derived cryptographic HMAC signing checks.</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
