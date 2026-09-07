import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router';
import { Input } from '../components/Input';
import { Button } from '../components/Button';
import { AlertTriangle, CheckCircle2, KeyRound, Loader2, Lock } from 'lucide-react';
import { registerAccount } from '../../utils/api';

export function CreatePassword() {
  const navigate = useNavigate();
  const location = useLocation();
  const [formData, setFormData] = useState({
    password: '',
    confirmPassword: '',
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const getPasswordStrength = (password: string) => {
    if (password.length < 8) return { strength: 'weak', color: 'bg-destructive', width: '33%' };
    if (password.length >= 10 && /[A-Z]/.test(password) && /[0-9]/.test(password)) {
      return { strength: 'strong', color: 'bg-emerald-500', width: '100%' };
    }
    return { strength: 'medium', color: 'bg-amber-500', width: '66%' };
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    const { username, nid, activationCode, bp = '123456' } = location.state || {};

    if (!username || !nid || !activationCode) {
      setError('Missing activation information. Please restart bank-assisted registration.');
      return;
    }

    setIsLoading(true);

    try {
      const result = await registerAccount({
        username,
        password: formData.password,
        nid,
        activationCode,
        bp,
      });

      if (result.status === 'success') {
        navigate('/activation-success', { state: { username } });
      } else {
        setError(result.message || 'Registration failed');
      }
    } catch (err) {
      setError('An unexpected error occurred during registration.');
    } finally {
      setIsLoading(false);
    }
  };

  const passwordStrength = formData.password ? getPasswordStrength(formData.password) : null;

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center p-4">
      <div className="max-w-4xl w-full grid gap-6 md:grid-cols-[360px_1fr]">
        <aside className="rounded-lg bg-[#2563EB] text-white p-6">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-lg bg-white/15 mb-5">
            <KeyRound size={26} />
          </div>
          <h1 className="text-white mb-2">Create private K2</h1>
          <p className="text-sm text-white/80">
            Your password is stretched with PBKDF2-SHA256 using NID/BRC as salt. The stretched value becomes K2 for AES encryption.
          </p>

          <div className="mt-6 space-y-3 text-sm">
            <div className="rounded-lg bg-white/10 p-3">
              <p className="text-white/70">BP</p>
              <p className="font-mono text-lg">123456</p>
            </div>
            <div className="rounded-lg bg-white/10 p-3">
              <p className="text-white/70">Timestamp T</p>
              <p>Created now and updated after successful transfer.</p>
            </div>
          </div>
        </aside>

        <section className="rounded-lg bg-white border border-border p-6 shadow-sm">
          <div className="flex items-center gap-3 mb-5">
            <div className="h-10 w-10 rounded-lg bg-[#EFF6FF] text-[#2563EB] flex items-center justify-center">
              <Lock size={22} />
            </div>
            <div>
              <h2>Set your password</h2>
              <p className="text-sm text-muted-foreground">Only the user should know this value.</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Create Password"
              showK2Label
              isPassword
              placeholder="Minimum 8 characters"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              required
            />

            {passwordStrength && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">K2 strength</span>
                  <span className="font-medium capitalize">{passwordStrength.strength}</span>
                </div>
                <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                  <div className={`h-full ${passwordStrength.color}`} style={{ width: passwordStrength.width }} />
                </div>
              </div>
            )}

            <Input
              label="Confirm Password"
              isPassword
              placeholder="Re-enter password"
              value={formData.confirmPassword}
              onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
              error={error}
              required
            />

            <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 flex gap-3">
              <AlertTriangle size={20} className="text-amber-600 shrink-0 mt-0.5" />
              <p className="text-sm text-amber-900">
                The bank cannot recover this password. If it is forgotten, the account must be re-activated at the branch.
              </p>
            </div>

            <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 flex gap-3">
              <CheckCircle2 size={20} className="text-emerald-600 shrink-0 mt-0.5" />
              <p className="text-sm text-emerald-900">
                Registration will create your Supabase Auth user, profile, account, and first notification.
              </p>
            </div>

            <Button type="submit" fullWidth disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Activating...
                </>
              ) : (
                'Activate Account'
              )}
            </Button>
          </form>
        </section>
      </div>
    </div>
  );
}
