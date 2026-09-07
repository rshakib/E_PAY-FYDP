import { useState } from 'react';
import { useNavigate } from 'react-router';
import { Sidebar } from '../components/Sidebar';
import { Navbar } from '../components/Navbar';
import { ArrowLeft, Clock, Landmark, Info } from 'lucide-react';

export function CashOut() {
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

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

        <main className="flex-1 p-6 space-y-6 max-w-4xl w-full mx-auto flex flex-col">
          {/* Header */}
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate(-1)}
              className="w-10 h-10 bg-white border border-slate-200 rounded-full flex items-center justify-center hover:bg-slate-50 transition-colors shadow-sm cursor-pointer"
            >
              <ArrowLeft size={18} className="text-slate-600" />
            </button>
            <div>
              <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">Cash Out</h1>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mt-0.5">Withdraw digital funds into physical cash</p>
            </div>
          </div>

          {/* Placeholder Panel */}
          <div className="flex-1 flex items-center justify-center py-12">
            <div className="bg-white rounded-3xl p-8 shadow-sm border border-slate-250/65 max-w-md w-full text-center space-y-6">
              <div className="w-16 h-16 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center mx-auto shadow-sm">
                <Clock size={30} className="animate-pulse" />
              </div>
              
              <div>
                <span className="text-[10px] font-black uppercase tracking-widest text-blue-600 bg-blue-50 px-2.5 py-1 rounded-full">
                  Planned for Future Release
                </span>
                <h2 className="text-slate-800 font-extrabold text-lg mt-4">Cash Out Feature coming soon</h2>
                <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                  We are developing a secure, geolocation-based banking agent withdrawal workflow. 
                  This will allow you to cash out funds securely from authorized local points.
                </p>
              </div>

              <div className="border-t border-slate-100 pt-5 text-left space-y-3">
                <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wide flex items-center gap-1.5">
                  <Landmark size={14} className="text-blue-500" />
                  Planned Specifications
                </h4>
                <ul className="text-xs text-slate-500 space-y-2">
                  <li className="flex gap-2">
                    <span>•</span>
                    <span><strong>1.85% Service Fee:</strong> Standard withdrawal processing tariff.</span>
                  </li>
                  <li className="flex gap-2">
                    <span>•</span>
                    <span><strong>Agent Locator:</strong> Geolocation list to select nearby terminals.</span>
                  </li>
                  <li className="flex gap-2">
                    <span>•</span>
                    <span><strong>Biometric Verify:</strong> Multi-key K1 + K2 + BP verification.</span>
                  </li>
                </ul>
              </div>

              <div className="bg-blue-50/60 border border-blue-100 rounded-2xl p-4 text-left flex items-start gap-2.5">
                <Info size={16} className="text-blue-600 shrink-0 mt-0.5" />
                <p className="text-[10px] font-semibold text-blue-800 leading-relaxed">
                  The withdrawal payload is planned to utilize AES-CBC encryption and SHA-256 HMAC integrity signatures 
                  to align with the core paper security pipeline.
                </p>
              </div>

              <button
                onClick={() => navigate('/dashboard')}
                className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-extrabold transition-colors cursor-pointer active:scale-95"
              >
                Back to Dashboard
              </button>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
