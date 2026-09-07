import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import { Sidebar } from '../components/Sidebar';
import { Navbar } from '../components/Navbar';
import { Input } from '../components/Input';
import { Button } from '../components/Button';
import { 
  ArrowLeft, Palette, Globe, Coins, Settings as SettingsIcon, 
  UserCheck, Bell, Shield, Info, CheckCircle, RotateCcw, Save 
} from 'lucide-react';
import { getUserSession } from '../../utils/session';

export function Settings() {
  const navigate = useNavigate();
  const session = getUserSession();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Default initial values
  const defaultValues = {
    darkMode: false,
    language: 'en',
    currency: 'bdt',
    displayName: '',
    txAlerts: true,
    emailAlerts: false,
  };

  // State hooks
  const [darkMode, setDarkMode] = useState(defaultValues.darkMode);
  const [language, setLanguage] = useState(defaultValues.language);
  const [currency, setCurrency] = useState(defaultValues.currency);
  const [displayName, setDisplayName] = useState(defaultValues.displayName);
  const [txAlerts, setTxAlerts] = useState(defaultValues.txAlerts);
  const [emailAlerts, setEmailAlerts] = useState(defaultValues.emailAlerts);
  
  // Notification Toast state
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    if (!session) {
      navigate('/login');
      return;
    }
    // Set default display name based on session username
    const initialName = session.username === 'tester1' ? 'Tester One' : session.username === 'tester2' ? 'Tester Two' : session.username;
    setDisplayName(initialName);
  }, [session]);

  if (!session) {
    return null;
  }

  const handleDiscard = () => {
    if (confirm('Discard all unsaved preferences changes?')) {
      setDarkMode(defaultValues.darkMode);
      setLanguage(defaultValues.language);
      setCurrency(defaultValues.currency);
      const resetName = session.username === 'tester1' ? 'Tester One' : session.username === 'tester2' ? 'Tester Two' : session.username;
      setDisplayName(resetName);
      setTxAlerts(defaultValues.txAlerts);
      setEmailAlerts(defaultValues.emailAlerts);
    }
  };

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 3000);
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
              <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">App Settings</h1>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mt-0.5">Customize display preferences & notifications</p>
            </div>
          </div>

          {saveSuccess && (
            <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-4 flex items-center gap-3 text-emerald-800 text-sm font-bold animate-in fade-in slide-in-from-top-2 duration-300">
              <CheckCircle size={20} className="text-emerald-600 shrink-0" />
              <span>Preferences saved successfully! (Note: Changes stored in temporary local state)</span>
            </div>
          )}

          <form onSubmit={handleSave} className="grid grid-cols-1 lg:grid-cols-[1fr_380px] gap-6 items-start">
            {/* Left Column: Display and Preferences */}
            <div className="space-y-6">
              {/* Display & Appearance */}
              <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-200 space-y-5">
                <h3 className="text-slate-800 font-extrabold text-base tracking-tight pb-3 border-b border-slate-100 flex items-center gap-2">
                  <Palette size={18} className="text-blue-600" />
                  Display & Appearance
                </h3>

                {/* Theme Mode Toggle */}
                <div className="flex items-center justify-between p-4 bg-slate-50 border border-slate-100 rounded-2xl">
                  <div>
                    <h4 className="text-sm font-bold text-slate-800">Theme Dark Mode</h4>
                    <p className="text-[10px] font-semibold text-slate-400 mt-0.5">Toggle default application dark backdrop (UI only)</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setDarkMode(!darkMode)}
                    className={`w-12 h-6 rounded-full transition-all duration-300 relative focus:outline-none border border-slate-200 cursor-pointer ${
                      darkMode ? 'bg-blue-600' : 'bg-slate-200'
                    }`}
                  >
                    <span 
                      className={`w-5 h-5 rounded-full bg-white absolute top-0.5 shadow-sm transition-all duration-300 ${
                        darkMode ? 'left-6' : 'left-0.5'
                      }`}
                    />
                  </button>
                </div>

                {/* Language Dropdown Selector */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                      <Globe size={14} className="text-slate-400" />
                      App Language
                    </label>
                    <select
                      value={language}
                      onChange={(e) => setLanguage(e.target.value)}
                      className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all cursor-pointer"
                    >
                      <option value="en">English (US)</option>
                      <option value="bn">Bangla (BD)</option>
                    </select>
                  </div>

                  {/* Currency Selector */}
                  <div className="space-y-2">
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                      <Coins size={14} className="text-slate-400" />
                      Default Currency
                    </label>
                    <select
                      value={currency}
                      onChange={(e) => setCurrency(e.target.value)}
                      className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all cursor-pointer"
                    >
                      <option value="bdt">Bangladeshi Taka (৳)</option>
                      <option value="usd">US Dollar (USD)</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Preferences */}
              <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-200 space-y-6">
                <h3 className="text-slate-800 font-extrabold text-base tracking-tight pb-3 border-b border-slate-100 flex items-center gap-2">
                  <UserCheck size={18} className="text-blue-600" />
                  Preferences
                </h3>

                {/* Display Name Input */}
                <div>
                  <Input
                    label="Wallet Display Name"
                    type="text"
                    placeholder="Enter wallet display name"
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    required
                  />
                  <p className="text-[10px] font-semibold text-slate-400 mt-1.5">
                    Your display name appears on internal invoices and notification ledgers.
                  </p>
                </div>

                {/* Notifications Preferences */}
                <div className="space-y-4 pt-2">
                  <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                    <Bell size={14} className="text-slate-400" />
                    Alerts & Notifications
                  </h4>

                  {/* Transaction Alerts Switch */}
                  <div className="flex items-center justify-between p-4 bg-slate-50 border border-slate-100 rounded-2xl">
                    <div>
                      <h5 className="text-sm font-bold text-slate-800">Transaction Alerts</h5>
                      <p className="text-[10px] font-semibold text-slate-400 mt-0.5">Receive instant alerts for incoming and outgoing payments</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => setTxAlerts(!txAlerts)}
                      className={`w-12 h-6 rounded-full transition-all duration-300 relative focus:outline-none border border-slate-200 cursor-pointer ${
                        txAlerts ? 'bg-blue-600' : 'bg-slate-200'
                      }`}
                    >
                      <span 
                        className={`w-5 h-5 rounded-full bg-white absolute top-0.5 shadow-sm transition-all duration-300 ${
                          txAlerts ? 'left-6' : 'left-0.5'
                        }`}
                      />
                    </button>
                  </div>

                  {/* Email Alerts Switch */}
                  <div className="flex items-center justify-between p-4 bg-slate-50 border border-slate-100 rounded-2xl">
                    <div>
                      <h5 className="text-sm font-bold text-slate-800">Email Notifications</h5>
                      <p className="text-[10px] font-semibold text-slate-400 mt-0.5">Monthly statement reports and key activity security logs</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => setEmailAlerts(!emailAlerts)}
                      className={`w-12 h-6 rounded-full transition-all duration-300 relative focus:outline-none border border-slate-200 cursor-pointer ${
                        emailAlerts ? 'bg-blue-600' : 'bg-slate-200'
                      }`}
                    >
                      <span 
                        className={`w-5 h-5 rounded-full bg-white absolute top-0.5 shadow-sm transition-all duration-300 ${
                          emailAlerts ? 'left-6' : 'left-0.5'
                        }`}
                      />
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column: App Info and Actions */}
            <div className="space-y-6">
              {/* Application Info Card */}
              <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-200 space-y-4">
                <h3 className="text-slate-800 font-extrabold text-base tracking-tight pb-3 border-b border-slate-100 flex items-center gap-2 mb-1">
                  <Info size={18} className="text-blue-600" />
                  Application Info
                </h3>

                <div className="space-y-3">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-semibold text-slate-400">App Version</span>
                    <span className="font-bold text-slate-800 bg-slate-100 px-2 py-0.5 rounded-lg">v1.2.0-beta</span>
                  </div>
                  <div className="flex justify-between items-center text-xs border-t border-slate-50 pt-3">
                    <span className="font-semibold text-slate-400">Build Status</span>
                    <span className="font-black text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-lg border border-emerald-100 uppercase tracking-wide">
                      Passed
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-xs border-t border-slate-50 pt-3">
                    <span className="font-semibold text-slate-400">Environment</span>
                    <span className="font-bold text-slate-600">Sandbox TLS</span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="space-y-2.5">
                <Button 
                  type="submit" 
                  fullWidth
                  className="flex items-center justify-center gap-2 py-3.5 font-bold"
                >
                  <Save size={16} />
                  Save Preferences
                </Button>
                <button
                  type="button"
                  onClick={handleDiscard}
                  className="w-full flex items-center justify-center gap-2 py-3.5 border-2 border-slate-200 hover:border-slate-400 text-slate-600 hover:bg-slate-50 rounded-2xl text-xs font-black transition-colors cursor-pointer active:scale-95"
                >
                  <RotateCcw size={14} />
                  Discard Changes
                </button>
              </div>
            </div>
          </form>
        </main>
      </div>
    </div>
  );
}
