import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import { Sidebar } from '../components/Sidebar';
import { Navbar } from '../components/Navbar';
import { Button } from '../components/Button';
import { 
  User, Mail, Phone, Laptop, Smartphone, LogOut, Camera, 
  CheckCircle, ArrowLeft, MapPin, Clock, ShieldCheck 
} from 'lucide-react';
import { getUserSession, clearUserSession } from '../../utils/session';

interface Device {
  id: string;
  name: string;
  type: 'mobile' | 'desktop';
  location: string;
  lastActive: string;
  isCurrent: boolean;
}

export function Profile() {
  const navigate = useNavigate();
  const session = getUserSession();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    if (!session) {
      navigate('/login');
    }
  }, [session]);

  if (!session) {
    return null;
  }

  // Derive mock profile information matching the logged-in user session
  const username = session.username;
  const fullName = username === 'tester1' ? 'Tester One' : username === 'tester2' ? 'Tester Two' : username.charAt(0).toUpperCase() + username.slice(1);
  const email = `${username}@niropay.com`;
  const phone = username === 'tester1' ? '+880 1712-345678' : username === 'tester2' ? '+880 1712-345679' : '+880 1700-000000';

  const mockDevices: Device[] = [
    {
      id: 'dev-1',
      name: 'Google Pixel 8 Pro',
      type: 'mobile',
      location: 'Dhaka, Bangladesh',
      lastActive: 'Active Now',
      isCurrent: true
    },
    {
      id: 'dev-2',
      name: 'Windows PC • Chrome',
      type: 'desktop',
      location: 'Dhaka, Bangladesh',
      lastActive: '2 hours ago',
      isCurrent: false
    }
  ];

  const handleLogoutAll = () => {
    if (confirm('Are you sure you want to log out from all devices? This will invalidate all active sessions.')) {
      clearUserSession();
      navigate('/login');
    }
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
              <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">My Profile</h1>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mt-0.5">Manage personal information & security settings</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-[300px_1fr] gap-6 items-start">
            {/* Left Column: Avatar and Verified Status */}
            <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-200 flex flex-col items-center text-center space-y-4">
              {/* Avatar Uploader UI */}
              <div className="relative group">
                <div className="w-28 h-28 rounded-full bg-blue-100 border-4 border-blue-50 flex items-center justify-center text-blue-600 text-3xl font-black shadow-inner select-none">
                  {username.slice(0, 2).toUpperCase()}
                </div>
                {/* Camera Overlay Icon */}
                <button 
                  type="button"
                  title="Upload profile picture (UI only)"
                  className="absolute bottom-1 right-1 w-9 h-9 bg-blue-600 text-white rounded-full flex items-center justify-center shadow-md hover:bg-blue-700 transition-colors cursor-pointer border-2 border-white active:scale-95"
                >
                  <Camera size={16} />
                </button>
              </div>

              {/* Name & Handle */}
              <div>
                <h2 className="text-lg font-black text-slate-800 tracking-tight">{fullName}</h2>
                <p className="text-xs font-semibold text-slate-400">@{username}</p>
              </div>

              {/* Verified Account Badge */}
              <div className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 border border-blue-100 rounded-2xl">
                <ShieldCheck size={16} className="text-blue-600" />
                <span className="text-[10px] font-black text-blue-700 uppercase tracking-wide">Verified Account</span>
              </div>

              <div className="w-full border-t border-slate-100 pt-4 text-left space-y-4">
                <div>
                  <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest block mb-1">Account Category</span>
                  <span className="text-xs font-bold text-slate-700">Petty Cash Wallet</span>
                </div>

                <div className="space-y-2">
                  <button
                    onClick={() => navigate('/security')}
                    className="w-full flex items-center justify-center gap-2 py-2.5 border border-slate-200 hover:border-blue-600 hover:text-blue-600 text-slate-600 text-xs font-extrabold rounded-2xl transition-colors cursor-pointer"
                  >
                    Go to Security Center
                  </button>
                  <button
                    onClick={() => navigate('/settings')}
                    className="w-full flex items-center justify-center gap-2 py-2.5 border border-slate-200 hover:border-blue-600 hover:text-blue-600 text-slate-600 text-xs font-extrabold rounded-2xl transition-colors cursor-pointer"
                  >
                    Configure Settings
                  </button>
                </div>
              </div>
            </div>

            {/* Right Column: Personal Information & Linked Devices */}
            <div className="space-y-6">
              {/* Personal Information Cards */}
              <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-200">
                <h3 className="mb-4 text-slate-800 font-extrabold text-base tracking-tight">Personal Information</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {/* Full Name Card */}
                  <div className="p-4 bg-slate-50 border border-slate-100 rounded-2xl flex items-center gap-3">
                    <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center text-slate-600 shadow-sm border border-slate-100 shrink-0">
                      <User size={18} />
                    </div>
                    <div>
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Full Name</span>
                      <span className="text-sm font-bold text-slate-800 leading-snug">{fullName}</span>
                    </div>
                  </div>

                  {/* Email Address Card */}
                  <div className="p-4 bg-slate-50 border border-slate-100 rounded-2xl flex items-center gap-3">
                    <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center text-slate-600 shadow-sm border border-slate-100 shrink-0">
                      <Mail size={18} />
                    </div>
                    <div>
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Email Address</span>
                      <span className="text-sm font-bold text-slate-800 leading-snug truncate max-w-[180px] block">{email}</span>
                    </div>
                  </div>

                  {/* Username Card */}
                  <div className="p-4 bg-slate-50 border border-slate-100 rounded-2xl flex items-center gap-3">
                    <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center text-slate-600 shadow-sm border border-slate-100 shrink-0">
                      <User size={18} />
                    </div>
                    <div>
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Username</span>
                      <span className="text-sm font-bold text-slate-800 leading-snug">@{username}</span>
                    </div>
                  </div>

                  {/* Phone Number Card */}
                  <div className="p-4 bg-slate-50 border border-slate-100 rounded-2xl flex items-center gap-3">
                    <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center text-slate-600 shadow-sm border border-slate-100 shrink-0">
                      <Phone size={18} />
                    </div>
                    <div>
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Phone Number</span>
                      <span className="text-sm font-bold text-slate-800 leading-snug">{phone}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Linked Devices Section */}
              <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-200">
                <h3 className="mb-4 text-slate-800 font-extrabold text-base tracking-tight">Linked Devices</h3>
                <div className="space-y-3">
                  {mockDevices.map((dev) => {
                    const Icon = dev.type === 'mobile' ? Smartphone : Laptop;
                    return (
                      <div 
                        key={dev.id}
                        className="flex items-center justify-between p-4 bg-slate-50 border border-slate-100 rounded-2xl"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center text-slate-600 shadow-sm border border-slate-100 shrink-0">
                            <Icon size={18} />
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-bold text-slate-800">{dev.name}</span>
                              {dev.isCurrent && (
                                <span className="text-[9px] font-black text-blue-700 bg-blue-100 px-1.5 py-0.5 rounded-lg uppercase tracking-wide">
                                  Current
                                </span>
                              )}
                            </div>
                            <div className="flex items-center gap-1.5 text-[10px] font-semibold text-slate-400 mt-0.5">
                              <MapPin size={10} />
                              <span>{dev.location}</span>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-1.5 text-xs font-bold text-slate-500">
                          <Clock size={12} className="text-slate-400" />
                          <span>{dev.lastActive}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Logout actions */}
              <div className="flex justify-end pt-2">
                <button
                  onClick={handleLogoutAll}
                  className="inline-flex items-center gap-2.5 px-5 py-3 border-2 border-red-200 hover:border-red-500 text-red-600 hover:bg-red-50 rounded-2xl text-xs font-black transition-colors cursor-pointer active:scale-95 shadow-sm"
                >
                  <LogOut size={14} className="text-red-500" />
                  Logout From All Devices
                </button>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
