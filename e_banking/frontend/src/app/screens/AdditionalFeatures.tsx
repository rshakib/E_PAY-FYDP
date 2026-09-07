import { useState } from 'react';
import { useNavigate } from 'react-router';
import { Input } from '../components/Input';
import { Button } from '../components/Button';
import {
  ArrowLeft,
  Mail,
  QrCode,
  Smartphone,
  CreditCard,
  CheckCircle,
  Camera,
  Nfc,
} from 'lucide-react';
import { motion } from 'motion/react';

export function AdditionalFeatures() {
  const navigate = useNavigate();
  const [activeSection, setActiveSection] = useState<string | null>(null);
  const [email, setEmail] = useState('');
  const [emailVerified, setEmailVerified] = useState(false);
  const [showQRScanner, setShowQRScanner] = useState(false);
  const [showNFC, setShowNFC] = useState(false);
  const [linkedCards, setLinkedCards] = useState<string[]>([]);

  const handleEmailVerify = () => {
    if (email) {
      setTimeout(() => {
        setEmailVerified(true);
        alert(`Verification email sent to ${email}`);
      }, 500);
    }
  };

  const handleQRScan = () => {
    setShowQRScanner(true);
    setTimeout(() => {
      setShowQRScanner(false);
      alert('QR Code scanned: @merchant_store_001');
    }, 2000);
  };

  const handleNFCTap = () => {
    setShowNFC(true);
    setTimeout(() => {
      setShowNFC(false);
      alert('NFC payment of ৳150 completed');
    }, 2000);
  };

  const handleLinkCard = () => {
    const cardNumber = prompt('Enter card number (last 4 digits):');
    if (cardNumber && cardNumber.length === 4) {
      setLinkedCards([...linkedCards, `**** **** **** ${cardNumber}`]);
    }
  };



  const features = [
    {
      id: 'email',
      icon: Mail,
      title: 'Email Verification',
      description: 'Add email for account recovery',
      color: 'bg-blue-500',
    },
    {
      id: 'qr',
      icon: QrCode,
      title: 'QR Code Scanner',
      description: 'Scan merchant QR codes',
      color: 'bg-purple-500',
    },
    {
      id: 'nfc',
      icon: Nfc,
      title: 'NFC Tap-to-Pay',
      description: 'Contactless payments',
      color: 'bg-emerald-500',
    },
    {
      id: 'card',
      icon: CreditCard,
      title: 'Card Linking',
      description: 'Link credit/debit cards',
      color: 'bg-amber-500',
    },

  ];

  return (
    <div className="min-h-screen bg-background">
      <div className="bg-gradient-to-r from-[#2563EB] to-blue-600 text-white px-4 py-6">
        <div className="max-w-2xl mx-auto flex items-center gap-4">
          <button
            onClick={() => navigate(-1)}
            className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center hover:bg-white/30 transition-colors"
          >
            <ArrowLeft size={20} />
          </button>
          <div>
            <h1 className="text-white mb-1">Additional Features</h1>
            <p className="text-sm text-white/80">Extended functionality beyond core thesis</p>
          </div>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 gap-4 mb-6">
          {features.map((feature) => {
            const Icon = feature.icon;
            const isActive = activeSection === feature.id;

            return (
              <motion.div
                key={feature.id}
                layout
                className="bg-white rounded-2xl shadow-lg border border-border overflow-hidden"
              >
                <button
                  onClick={() => setActiveSection(isActive ? null : feature.id)}
                  className="w-full flex items-center gap-4 p-5 hover:bg-muted/50 transition-colors"
                >
                  <div className={`flex-shrink-0 w-12 h-12 ${feature.color} rounded-full flex items-center justify-center`}>
                    <Icon size={24} className="text-white" />
                  </div>
                  <div className="flex-1 text-left">
                    <h3 className="mb-1">{feature.title}</h3>
                    <p className="text-sm text-muted-foreground">{feature.description}</p>
                  </div>
                  <div className={`transform transition-transform ${isActive ? 'rotate-180' : ''}`}>
                    <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M6 9l4 4 4-4" />
                    </svg>
                  </div>
                </button>

                {isActive && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="border-t border-border bg-muted/30"
                  >
                    <div className="p-5">
                      {feature.id === 'email' && (
                        <div className="space-y-4">
                          <Input
                            label="Email Address"
                            type="email"
                            placeholder="your.email@example.com"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                          />
                          {emailVerified ? (
                            <div className="flex items-center gap-2 text-emerald-600 bg-emerald-50 p-3 rounded-lg">
                              <CheckCircle size={20} />
                              <span className="text-sm font-medium">Email verified!</span>
                            </div>
                          ) : (
                            <Button onClick={handleEmailVerify} disabled={!email}>
                              Send Verification Email
                            </Button>
                          )}
                          <p className="text-xs text-muted-foreground">
                            Email can be used for account notifications and recovery assistance.
                          </p>
                        </div>
                      )}

                      {feature.id === 'qr' && (
                        <div className="space-y-4">
                          {showQRScanner ? (
                            <div className="relative bg-black rounded-xl overflow-hidden aspect-square max-w-xs mx-auto">
                              <motion.div
                                animate={{ y: [0, 200, 0] }}
                                transition={{ repeat: Infinity, duration: 2 }}
                                className="absolute inset-x-0 top-0 h-1 bg-[#2563EB] shadow-lg shadow-[#2563EB]/50"
                              />
                              <div className="absolute inset-4 border-2 border-white rounded-xl" />
                              <div className="absolute inset-0 flex items-center justify-center">
                                <Camera size={48} className="text-white/50" />
                              </div>
                            </div>
                          ) : (
                            <div className="text-center py-8">
                              <QrCode size={64} className="text-[#2563EB] mx-auto mb-4" />
                              <h4 className="mb-2">Scan Merchant QR Code</h4>
                              <p className="text-sm text-muted-foreground mb-4">
                                Point your camera at the merchant's QR code to quickly initiate payment
                              </p>
                              <Button onClick={handleQRScan}>
                                Start Scanner
                              </Button>
                            </div>
                          )}
                        </div>
                      )}

                      {feature.id === 'nfc' && (
                        <div className="space-y-4">
                          {showNFC ? (
                            <div className="text-center py-12">
                              <motion.div
                                animate={{ scale: [1, 1.2, 1] }}
                                transition={{ repeat: Infinity, duration: 1.5 }}
                                className="inline-flex items-center justify-center w-24 h-24 bg-emerald-100 rounded-full mb-4"
                              >
                                <Nfc size={48} className="text-emerald-600" />
                              </motion.div>
                              <p className="font-medium">Hold device near terminal...</p>
                            </div>
                          ) : (
                            <div className="text-center py-8">
                              <Smartphone size={64} className="text-[#2563EB] mx-auto mb-4" />
                              <h4 className="mb-2">NFC Tap-to-Pay</h4>
                              <p className="text-sm text-muted-foreground mb-4">
                                Make contactless payments by tapping your phone on NFC terminals
                              </p>
                              <Button onClick={handleNFCTap}>
                                Simulate NFC Payment
                              </Button>
                              <p className="text-xs text-muted-foreground mt-4">
                                Requires NFC-enabled device and merchant terminal
                              </p>
                            </div>
                          )}
                        </div>
                      )}

                      {feature.id === 'card' && (
                        <div className="space-y-4">
                          <div className="space-y-3">
                            {linkedCards.length === 0 ? (
                              <div className="text-center py-6 bg-muted/50 rounded-xl">
                                <p className="text-sm text-muted-foreground">No cards linked</p>
                              </div>
                            ) : (
                              linkedCards.map((card, index) => (
                                <div
                                  key={index}
                                  className="flex items-center gap-3 p-4 bg-gradient-to-r from-[#2563EB] to-blue-600 rounded-xl text-white"
                                >
                                  <CreditCard size={24} />
                                  <span className="font-mono">{card}</span>
                                </div>
                              ))
                            )}
                          </div>
                          <Button onClick={handleLinkCard} fullWidth>
                            Link New Card
                          </Button>
                          <p className="text-xs text-muted-foreground">
                            Link credit or debit cards for backup payment methods. Cards are stored securely.
                          </p>
                        </div>
                      )}


                    </div>
                  </motion.div>
                )}
              </motion.div>
            );
          })}
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-xl p-5">
          <h4 className="text-sm font-medium text-blue-900 mb-2">Non-Thesis Extensions</h4>
          <p className="text-xs text-blue-800">
            These features extend beyond the core paper methodology (K1 + K2 + BP + HMAC + AES)
            to provide a complete modern e-payment experience. The thesis security model remains
            the foundation for all transaction processing.
          </p>
        </div>
      </div>
    </div>
  );
}
