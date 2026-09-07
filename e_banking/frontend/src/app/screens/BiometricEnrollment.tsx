import { useNavigate, useLocation } from 'react-router';
import { Button } from '../components/Button';
import { Fingerprint } from 'lucide-react';

const DEFAULT_BIOMETRIC_FINGERPRINT = '123456';

export function BiometricEnrollment() {
  const navigate = useNavigate();
  const location = useLocation();

  const handleContinue = () => {
    navigate('/create-password', {
      state: {
        ...(location.state || {}),
        bp: DEFAULT_BIOMETRIC_FINGERPRINT,
      },
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#EFF6FF] to-white flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-[#2563EB] rounded-full mb-4">
            <Fingerprint size={32} className="text-white" />
          </div>
          <h1 className="mb-2">Biometric Fingerprint</h1>
          <p className="text-muted-foreground">
            Default biometric fingerprint has been assigned.
          </p>
        </div>

        <div className="bg-white rounded-2xl p-8 shadow-lg border border-border mb-6">
          <div className="text-center">
            <p className="text-sm text-muted-foreground mb-2">Fingerprint BP</p>
            <p className="font-mono text-2xl text-[#2563EB]">{DEFAULT_BIOMETRIC_FINGERPRINT}</p>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-6">
            <p className="text-sm text-blue-900">
              This fixed BP value will be used for transaction encryption.
            </p>
          </div>
        </div>

        <Button fullWidth onClick={handleContinue}>
          Continue
        </Button>

        <button
          onClick={() => navigate(-1)}
          className="w-full mt-4 text-center text-muted-foreground hover:text-foreground underline"
        >
          Back
        </button>
      </div>
    </div>
  );
}
