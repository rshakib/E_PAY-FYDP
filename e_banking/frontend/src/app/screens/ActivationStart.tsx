import { useNavigate } from 'react-router';
import { Button } from '../components/Button';
import { BadgeCheck, FileKey2, KeyRound, ShieldCheck } from 'lucide-react';

const setupSteps = [
  {
    icon: BadgeCheck,
    title: 'Officer verification',
    text: 'Use the NID/BRC and activation code issued by the bank.',
  },
  {
    icon: FileKey2,
    title: 'K1 generation',
    text: 'The activation data creates the HMAC key used to verify each message.',
  },
  {
    icon: KeyRound,
    title: 'Private K2',
    text: 'Your password is stretched into the AES key material and is never shown to an officer.',
  },
];

export function ActivationStart() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center p-4">
      <div className="max-w-5xl w-full grid gap-6 md:grid-cols-[1fr_420px] items-stretch">
        <section className="rounded-lg bg-[#2563EB] text-white p-6 md:p-8 flex flex-col justify-between">
          <div>
            <div className="inline-flex h-12 w-12 items-center justify-center rounded-lg bg-white/15 mb-6">
              <ShieldCheck size={28} />
            </div>
            <h1 className="text-white text-3xl md:text-4xl leading-tight mb-3">
              E-Payment Activation
            </h1>
            <p className="text-white/85 max-w-xl">
              A bank-assisted setup for petty cash payments using HMAC integrity, AES encryption, fingerprint BP, and a rotating timestamp T.
            </p>
          </div>

          <div className="grid gap-3 mt-8">
            {setupSteps.map((step) => {
              const Icon = step.icon;
              return (
                <div key={step.title} className="flex gap-3 rounded-lg bg-white/10 p-4">
                  <Icon size={22} className="mt-0.5 shrink-0" />
                  <div>
                    <h3 className="text-white text-base">{step.title}</h3>
                    <p className="text-sm text-white/75">{step.text}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        <section className="rounded-lg border border-border bg-white p-6 shadow-sm flex flex-col justify-center">
          <h2 className="mb-2">Start secure registration</h2>
          <p className="text-sm text-muted-foreground mb-6">
            Continue only after your bank officer has verified your identity and issued an activation code.
          </p>

          <div className="space-y-3">
            <Button fullWidth onClick={() => navigate('/officer-verify')}>
              I have an activation code
            </Button>
            <Button fullWidth variant="outline" onClick={() => navigate('/login')}>
              Already registered
            </Button>
          </div>

          <div className="mt-6 rounded-lg bg-[#EFF6FF] p-4">
            <p className="text-sm text-[#1E40AF]">
              No OTP, no phone-number transfer, no SMS recovery. Transactions are username-to-username and verified by encrypted message integrity.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
