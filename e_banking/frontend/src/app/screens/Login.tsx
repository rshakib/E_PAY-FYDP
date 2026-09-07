import { useState } from 'react';
import { useNavigate } from 'react-router';
import { Input } from '../components/Input';
import { Button } from '../components/Button';
import { AlertCircle, KeyRound, Lock, ShieldCheck } from 'lucide-react';
import { saveUserSession } from '../../utils/session';
import { loginUser } from '../../utils/api';

export function Login() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const result = await loginUser(formData.username.trim(), formData.password);

      if (result.status !== 'success' || !result.user) {
        setError(result.message || 'Login failed. Please check your credentials.');
        setIsLoading(false);
        return;
      }

      const user = result.user;

      saveUserSession({
        id: user.id,
        username: user.username,
        token: result.token || '',
        t: user.t,
        balance: user.balance,
        accountId: user.accountId,
        daily_limit: user.daily_limit,
        today_spent: user.today_spent,
      });

      navigate('/dashboard');
    } catch (err) {
      setError('Authentication failed. Please try again.');
      console.error('Login error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center p-4">
      <div className="max-w-5xl w-full grid gap-6 md:grid-cols-[1fr_420px]">
        <section className="rounded-lg bg-white border border-border p-6 md:p-8 shadow-sm">
          <div className="flex items-center gap-3 mb-6">
            <div className="h-12 w-12 rounded-lg bg-[#EFF6FF] text-[#2563EB] flex items-center justify-center">
              <Lock size={26} />
            </div>
            <div>
              <h1>Account Login</h1>
              <p className="text-sm text-muted-foreground">Use your bank username and private K2 password.</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
                <AlertCircle size={20} className="text-red-600 shrink-0 mt-0.5" />
                <p className="text-sm font-medium text-red-900">{error}</p>
              </div>
            )}

            <Input
              label="Bank Username"
              type="text"
              placeholder="Enter bank-assigned username"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              helperText="Transfers are username-to-username only"
              required
              disabled={isLoading}
            />

            <Input
              label="Private Password"
              showK2Label
              isPassword
              placeholder="Enter your K2 password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              helperText="The backend verifies your password without exposing key material"
              required
              disabled={isLoading}
            />

            <Button type="submit" fullWidth disabled={isLoading}>
              {isLoading ? 'Verifying K2...' : 'Login'}
            </Button>
          </form>

          <div className="mt-5 flex items-center justify-between gap-3 text-sm">
            <button
              onClick={() => navigate('/')}
              className="text-[#2563EB] hover:underline"
            >
              Activate new account
            </button>
            <button
              onClick={() => alert('Please visit your bank branch for password reset')}
              className="text-muted-foreground hover:text-foreground hover:underline"
            >
              Forgot K2?
            </button>
          </div>
        </section>

        <aside className="rounded-lg bg-[#2563EB] text-white p-6 md:p-8">
          <ShieldCheck size={34} className="mb-5" />
          <h2 className="text-white mb-3">Paper-aligned security</h2>
          <div className="space-y-3">
            <div className="rounded-lg bg-white/10 p-4">
              <div className="flex items-center gap-2 mb-1">
                <KeyRound size={18} />
                <h3 className="text-white text-base">HMAC + AES</h3>
              </div>
              <p className="text-sm text-white/75">
                Transfer integrity and timestamp checks are handled by the backend without returning secret keys to the browser.
              </p>
            </div>
            <div className="rounded-lg bg-white/10 p-4">
              <p className="text-sm text-white/75">
                Successful transfers rotate timestamp T to reduce replay risk.
              </p>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
