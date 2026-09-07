import { useState } from 'react';
import { useNavigate } from 'react-router';
import { Input } from '../components/Input';
import { Button } from '../components/Button';
import { ArrowLeft, Fingerprint, KeyRound, ShieldCheck } from 'lucide-react';

export function OfficerVerify() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    nid: '',
    activationCode: '',
    username: '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.nid && formData.activationCode && formData.username) {
      navigate('/biometric-enrollment', { state: { ...formData, bp: '123456' } });
    }
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] p-4">
      <div className="max-w-5xl mx-auto py-6">
        <button
          onClick={() => navigate(-1)}
          className="mb-4 inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft size={18} />
          Back
        </button>

        <div className="grid gap-6 md:grid-cols-[380px_1fr]">
          <aside className="rounded-lg bg-white border border-border p-6 shadow-sm">
            <div className="inline-flex h-12 w-12 items-center justify-center rounded-lg bg-[#EFF6FF] text-[#2563EB] mb-5">
              <ShieldCheck size={26} />
            </div>
            <h1 className="mb-2">Bank officer verification</h1>
            <p className="text-sm text-muted-foreground">
              Enter the identity data verified at the branch. The backend derives K1 from activation code, identity number, username, and BP.
            </p>

            <div className="mt-6 space-y-3">
              <div className="flex gap-3 rounded-lg bg-[#F8FAFC] p-3">
                <KeyRound className="text-[#2563EB] shrink-0" size={20} />
                <p className="text-sm">K1 is used for HMAC F1/F2 message authentication.</p>
              </div>
              <div className="flex gap-3 rounded-lg bg-[#F8FAFC] p-3">
                <Fingerprint className="text-[#2563EB] shrink-0" size={20} />
                <p className="text-sm">BP is fixed to 123456 for the current prototype.</p>
              </div>
            </div>
          </aside>

          <section className="rounded-lg bg-white border border-border p-6 shadow-sm">
            <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                label="NID / BRC Number"
                type="text"
                placeholder="Verified identity number"
                value={formData.nid}
                onChange={(e) => setFormData({ ...formData, nid: e.target.value })}
                helperText="Used as K2 salt and as part of K1 derivation"
                required
              />

              <Input
                label="Activation Code"
                type="text"
                placeholder="Code provided by bank officer"
                value={formData.activationCode}
                onChange={(e) => setFormData({ ...formData, activationCode: e.target.value })}
                helperText="Used as the HMAC key source for registration"
                required
              />

              <Input
                label="Bank-Assigned Username"
                type="text"
                placeholder="Example: sohan"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value.trim() })}
                helperText="Transfers use usernames, not phone numbers"
                required
              />

              <Button type="submit" fullWidth>
                Continue to BP and K2
              </Button>
            </form>
          </section>
        </div>
      </div>
    </div>
  );
}
