import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router';
import { ArrowLeft, Bell, BellOff, Calendar } from 'lucide-react';
import { getUserSession } from '../../utils/session';
import { getNotifications } from '../../utils/api';

interface NotificationItem {
  id: string;
  title: string;
  message: string;
  created_at: string;
  is_read: boolean;
  notification_type?: string;
}

export function Notifications() {
  const navigate = useNavigate();
  const session = getUserSession();
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!session) {
      navigate('/login');
      return;
    }

    async function fetchNotifications() {
      try {
        const result = await getNotifications(session.username);
        if (result?.notifications) {
          setNotifications(result.notifications);
        }
      } catch (error) {
        console.error('Error fetching notifications:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchNotifications();
  }, [session, navigate]);

  if (!session) {
    return null;
  }

  return (
    <div className="min-h-screen bg-slate-50 font-sans">
      <div className="bg-blue-600 text-white px-4 py-6 shadow-md">
        <div className="max-w-2xl mx-auto flex items-center gap-4">
          <button
            onClick={() => navigate('/dashboard')}
            className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center hover:bg-white/30 transition-colors cursor-pointer"
            title="Back to Dashboard"
          >
            <ArrowLeft size={20} />
          </button>
          <div>
            <h1 className="text-white text-xl font-extrabold tracking-tight">Notifications</h1>
            <p className="text-xs text-blue-100 font-medium">Keep track of your transaction alerts and updates</p>
          </div>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-6">
        <div className="bg-white rounded-3xl shadow-sm border border-slate-200/60 overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <span className="text-sm font-bold text-slate-800">Recent Updates</span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-600">
              {notifications.filter(n => !n.is_read).length} Unread
            </span>
          </div>

          <div className="divide-y divide-slate-100">
            {loading ? (
              <div className="text-center py-12">
                <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
                <p className="text-sm text-slate-400 font-semibold">Loading notifications...</p>
              </div>
            ) : notifications.length > 0 ? (
              notifications.map((notif) => (
                <div
                  key={notif.id}
                  className={`p-4 transition-colors hover:bg-slate-50/70 flex gap-3.5 items-start ${
                    !notif.is_read ? 'bg-blue-50/30' : ''
                  }`}
                >
                  <div className={`p-2 rounded-xl shrink-0 ${
                    !notif.is_read ? 'bg-blue-50 text-blue-600' : 'bg-slate-100 text-slate-400'
                  }`}>
                    <Bell size={18} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <h4 className={`text-sm font-bold ${!notif.is_read ? 'text-slate-900' : 'text-slate-700'}`}>
                        {notif.title}
                      </h4>
                      {!notif.is_read && (
                        <span className="w-2.5 h-2.5 rounded-full bg-blue-600 shrink-0 mt-1.5" />
                      )}
                    </div>
                    <p className="text-xs text-slate-500 mt-1 leading-relaxed">{notif.message}</p>
                    <div className="flex items-center gap-1.5 text-[10px] text-slate-400 font-semibold mt-2">
                      <Calendar size={12} />
                      <span>{new Date(notif.created_at).toLocaleString()}</span>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-16 px-4">
                <div className="w-16 h-16 bg-slate-50 text-slate-300 rounded-full flex items-center justify-center mx-auto mb-4 border border-dashed border-slate-200">
                  <BellOff size={28} />
                </div>
                <h3 className="text-slate-800 font-bold text-base">All Caught Up!</h3>
                <p className="text-sm text-slate-400 mt-1.5 max-w-sm mx-auto">
                  You have no new notifications. We'll let you know when something comes up.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
