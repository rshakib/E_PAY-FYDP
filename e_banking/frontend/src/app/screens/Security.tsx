import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import { Sidebar } from '../components/Sidebar';
import { Navbar } from '../components/Navbar';
import { Button } from '../components/Button';
import { 
  ArrowLeft, Shield, Lock, Smartphone, History, Info, LockKeyhole 
} from 'lucide-react';
import { getUserSession } from '../../utils/session';

interface ActivityLog {
  time: string;
  ip: string;
  status: 'Success' | 'Failed';
  device: string;
}

export function Security() {
  const navigate = useNavigate();
  const session = getUserSession();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Local state for security settings
  const [securityScore, setSecurityScore] = useState(85);
  const [fingerprintEnabled, setFingerprintEnabled] = useState(true);
  const [faceIdEnabled, setFaceIdEnabled] = useState(false);
  // PIN Modal state
  const [showPinModal, setShowPinModal] = useState(false);
  const [currentPin, setCurrentPin] = useState('123456');
  const [newPin, setNewPin] = useState('');
  const [pinMessage, setPinMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!session) {
      navigate('/login');
    }
  }, [session]);

  if (!session) {
    return null;
  }

  const handleImproveScore = () => {
    if (securityScore < 100) {
      setSecurityScore(100);
      setFaceIdEnabled(true);
      alert('Security score optimized to 100%! Enabled Face ID login & audited encryption keys.');
    } else {
      alert('Your security score is already optimized at 100%!');
    }
  };

  const handlePinChangeSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (newPin.length !== 6 || !/^\d+$/.test(newPin)) {
      setPinMessage('PIN must be exactly 6 digits.');
      return;
    }
    setCurrentPin(newPin);
    setPinMessage('Security PIN updated successfully!');
    setNewPin('');
    setTimeout(() => {
      setShowPinModal(false);
      setPinMessage(null);
    }, 1500);
  };

  const mockActivityLogs: ActivityLog[] = [
    { time: 'Active Now', ip: '192.168.1.105', status: 'Success', device: 'Google Pixel 8 Pro' },
    { time: 'Today, 10:14 AM', ip: '192.168.1.105', status: 'Success', device: 'Windows PC • Chrome' },
    { time: 'Yesterday, 6:42 PM', ip: '103.220.10.82', status: 'Failed', device: 'Unknown Linux Device' },
  ];

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
              <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">Security Center</h1>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mt-0.5">Protect your funds & credentials</p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-[1fr_380px] gap-6 items-start">
            {/* Left Column: Score, Auth Settings */}
            <div className="space-y-6">
              {/* Security Score Card */}
              <div className="relative overflow-hidden bg-gradient-to-br from-blue-600 via-blue-700 to-blue-800 rounded-3xl p-6 shadow-lg text-white border border-blue-500/30">
                {/* Decorative background shapes */}
                <div className="absolute top-0 right-0 -mt-6 -mr-6 w-32 h-32 bg-white/10 rounded-full blur-2xl pointer-events-none" />
                <div className="absolute -bottom-8 -left-8 w-40 h-40 bg-blue-500/20 rounded-full blur-3xl pointer-events-none" />

                <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="space-y-3 flex-1">
                    <span className="text-[10px] font-black uppercase tracking-widest text-blue-100">Security Audit</span>
                    <h2 className="text-3xl font-extrabold tracking-tight">Security Score: {securityScore}%</h2>
                    
                    {/* Progress Bar */}
                    <div className="w-full bg-white/20 h-2.5 rounded-full overflow-hidden">
                      <div 
                        className="bg-white h-full transition-all duration-700 ease-out"
                        style={{ width: `${securityScore}%` }}
                      />
                    </div>

                    <p className="text-xs text-blue-100/90 font-medium leading-relaxed max-w-md">
                      {securityScore < 100 
                        ? 'Your account security is Good, but can be optimized. Complete pending security steps.' 
                        : 'Congratulations! Your account meets all high-level security recommendations.'
                      }
                    </p>
                  </div>
                  
                  <div className="shrink-0 flex items-center justify-start sm:justify-center">
                    <button
                      onClick={handleImproveScore}
                      className="px-5 py-3 bg-white hover:bg-blue-50 text-blue-700 font-extrabold text-xs rounded-2xl shadow-md transition-all active:scale-95 cursor-pointer"
                    >
                      {securityScore < 100 ? 'Improve Score' : 'Audit Complete'}
                    </button>
                  </div>
                </div>
              </div>

              {/* Authentication Settings */}
              <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-200 space-y-6">
                <h3 className="text-slate-800 font-extrabold text-base tracking-tight pb-3 border-b border-slate-100">
                  Authentication Settings
                </h3>

                {/* PIN Settings Row */}
                <div className="flex items-center justify-between p-4 bg-slate-50 border border-slate-100 rounded-2xl">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center text-slate-600 border border-slate-100 shadow-sm">
                      <LockKeyhole size={18} />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-slate-800">Security PIN</h4>
                      <p className="text-[10px] font-semibold text-slate-400 mt-0.5">Used for biometric confirmation checks</p>
                    </div>
                  </div>
                  <button
                    onClick={() => setShowPinModal(true)}
                    className="px-4 py-2 border border-slate-200 hover:border-blue-600 hover:bg-blue-50 hover:text-blue-600 rounded-xl text-xs font-extrabold text-slate-600 transition-colors cursor-pointer"
                  >
                    Change
                  </button>
                </div>

                {/* Fingerprint Toggle Row */}
                <div className="flex items-center justify-between p-4 bg-slate-50 border border-slate-100 rounded-2xl">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center text-slate-600 border border-slate-100 shadow-sm">
                      <Smartphone size={18} />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-slate-800">Fingerprint Login</h4>
                      <p className="text-[10px] font-semibold text-slate-400 mt-0.5">Quick fingerprint authentication verification</p>
                    </div>
                  </div>
                  {/* Switch toggle */}
                  <button
                    type="button"
                    onClick={() => setFingerprintEnabled(!fingerprintEnabled)}
                    className={`w-12 h-6 rounded-full transition-all duration-300 relative focus:outline-none border border-slate-200 cursor-pointer ${
                      fingerprintEnabled ? 'bg-blue-600' : 'bg-slate-200'
                    }`}
                  >
                    <span 
                      className={`w-5 h-5 rounded-full bg-white absolute top-0.5 shadow-sm transition-all duration-300 ${
                        fingerprintEnabled ? 'left-6' : 'left-0.5'
                      }`}
                    />
                  </button>
                </div>

                {/* Face ID Toggle Row */}
                <div className="flex items-center justify-between p-4 bg-slate-50 border border-slate-100 rounded-2xl">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center text-slate-600 border border-slate-100 shadow-sm">
                      <Shield size={18} />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-slate-800">Face ID Access</h4>
                      <p className="text-[10px] font-semibold text-slate-400 mt-0.5">Unlock application with facial recognition</p>
                    </div>
                  </div>
                  {/* Switch toggle */}
                  <button
                    type="button"
                    onClick={() => {
                      setFaceIdEnabled(!faceIdEnabled);
                      if(!faceIdEnabled) setSecurityScore(100);
                    }}
                    className={`w-12 h-6 rounded-full transition-all duration-300 relative focus:outline-none border border-slate-200 cursor-pointer ${
                      faceIdEnabled ? 'bg-blue-600' : 'bg-slate-200'
                    }`}
                  >
                    <span 
                      className={`w-5 h-5 rounded-full bg-white absolute top-0.5 shadow-sm transition-all duration-300 ${
                        faceIdEnabled ? 'left-6' : 'left-0.5'
                      }`}
                    />
                  </button>
                </div>
              </div>
            </div>

            {/* Right Column: Data Privacy & Recovery Key */}
            <div className="space-y-6">
              {/* Data & Privacy */}
              <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-200 space-y-4">
                <h3 className="text-slate-800 font-extrabold text-base tracking-tight pb-3 border-b border-slate-100 mb-1">
                  Data & Privacy
                </h3>

                {/* Padlock status info */}
                <div className="flex items-center justify-between p-2">
                  <div className="flex items-center gap-2.5">
                    <Lock className="text-blue-600 shrink-0" size={16} />
                    <span className="text-xs font-extrabold text-slate-600">Encryption Status</span>
                  </div>
                  <span className="text-[10px] font-black text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-lg border border-emerald-100 uppercase tracking-wider">
                    AES-256 Secured
                  </span>
                </div>

                {/* Session protection info */}
                <div className="flex items-center justify-between p-2 border-t border-slate-50 pt-3">
                  <div className="flex items-center gap-2.5">
                    <History className="text-blue-600 shrink-0" size={16} />
                    <span className="text-xs font-extrabold text-slate-600">HMAC Replay Guard</span>
                  </div>
                  <span className="text-[10px] font-black text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-lg border border-emerald-100 uppercase tracking-wider">
                    Active
                  </span>
                </div>

                {/* Login Activities logs */}
                <div className="border-t border-slate-100 pt-4 space-y-3">
                  <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest block">Recent Logins</span>
                  <div className="space-y-2">
                    {mockActivityLogs.map((log, idx) => (
                      <div key={idx} className="flex justify-between items-center text-[10px] bg-slate-50 p-2 rounded-xl border border-slate-100">
                        <div>
                          <p className="font-bold text-slate-700">{log.device}</p>
                          <p className="font-semibold text-slate-400">{log.time} • IP: {log.ip}</p>
                        </div>
                        <span className={`font-black ${
                          log.status === 'Success' ? 'text-emerald-600' : 'text-red-500'
                        }`}>
                          {log.status}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Settings Redirect Card */}
              <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-200 space-y-3">
                <h4 className="text-sm font-bold text-slate-800">Preferences & Alerts</h4>
                <p className="text-[11px] font-semibold text-slate-400 leading-relaxed">
                  Manage app languages, toggle dark mode, or configure custom transaction notifications.
                </p>
                <button
                  onClick={() => navigate('/settings')}
                  className="w-full flex items-center justify-center gap-2 py-2.5 border border-slate-200 hover:border-blue-600 hover:text-blue-600 text-slate-600 text-xs font-extrabold rounded-2xl transition-colors cursor-pointer"
                >
                  Configure Settings
                </button>
              </div>
            </div>
          </div>
        </main>
      </div>

      {/* Security PIN Change Modal */}
      {showPinModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <div className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm" onClick={() => setShowPinModal(false)} />
          {/* Modal Container */}
          <form 
            onSubmit={handlePinChangeSubmit}
            className="bg-white rounded-3xl p-6 shadow-xl border border-slate-200 max-w-sm w-full relative z-10 space-y-4 animate-in fade-in zoom-in-95 duration-200"
          >
            <div>
              <h3 className="text-slate-900 font-extrabold text-base tracking-tight">Change Security PIN</h3>
              <p className="text-xs font-semibold text-slate-400 mt-1">Configure your 6-digit confirmation PIN code</p>
            </div>

            <div className="p-3 bg-blue-50 text-blue-800 text-[10px] font-bold rounded-xl">
              Current Active PIN: <span className="font-mono">{currentPin}</span>
            </div>

            <div>
              <label className="block mb-1.5 text-xs font-bold text-slate-700">New 6-Digit PIN</label>
              <input
                type="password"
                maxLength={6}
                placeholder="******"
                value={newPin}
                onChange={(e) => setNewPin(e.target.value.replace(/\D/g, ''))}
                className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-center font-mono text-lg font-black tracking-widest focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            {pinMessage && (
              <p className={`text-xs font-bold flex items-center gap-1 ${
                pinMessage.includes('successful') ? 'text-emerald-600' : 'text-red-500'
              }`}>
                <Info size={14} />
                {pinMessage}
              </p>
            )}

            <div className="flex gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowPinModal(false)}
                className="flex-1 py-3 border border-slate-200 hover:bg-slate-50 text-slate-600 rounded-xl text-xs font-extrabold transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="flex-1 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-extrabold transition-colors cursor-pointer"
              >
                Update PIN
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
