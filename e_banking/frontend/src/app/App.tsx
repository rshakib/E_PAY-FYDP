import { BrowserRouter, Routes, Route, Navigate } from 'react-router';

import { ActivationStart } from './screens/ActivationStart';
import { OfficerVerify } from './screens/OfficerVerify';
import { BiometricEnrollment } from './screens/BiometricEnrollment';
import { CreatePassword } from './screens/CreatePassword';
import { ActivationSuccess } from './screens/ActivationSuccess';
import { Login } from './screens/Login';
import { Dashboard } from './screens/Dashboard';
import { SendMoney } from './screens/SendMoney';
import { TransactionProcessing } from './screens/TransactionProcessing';
import { TransactionResult } from './screens/TransactionResult';
import { TransactionHistory } from './screens/TransactionHistory';
import { AdditionalFeatures } from './screens/AdditionalFeatures';
import { Notifications } from './screens/Notifications';
import { MerchantPayment } from './screens/MerchantPayment';
import { MobileRecharge } from './screens/MobileRecharge';
import { BillPayment } from './screens/BillPayment';
import { Profile } from './screens/Profile';
import { Security } from './screens/Security';
import { Settings } from './screens/Settings';
import { QRPay } from './screens/QRPay';
import { MyQR } from './screens/MyQR';
import { CashOut } from './screens/CashOut';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ActivationStart />} />
        <Route path="/officer-verify" element={<OfficerVerify />} />
        <Route path="/biometric-enrollment" element={<BiometricEnrollment />} />
        <Route path="/create-password" element={<CreatePassword />} />
        <Route path="/activation-success" element={<ActivationSuccess />} />
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/send-money" element={<SendMoney />} />
        <Route path="/merchant" element={<MerchantPayment />} />
        <Route path="/recharge" element={<MobileRecharge />} />
        <Route path="/bills" element={<BillPayment />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/security" element={<Security />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/qr-pay" element={<QRPay />} />
        <Route path="/my-qr" element={<MyQR />} />
        <Route path="/cashout" element={<CashOut />} />
        <Route path="/transaction-processing" element={<TransactionProcessing />} />
        <Route path="/transaction-result" element={<TransactionResult />} />
        <Route path="/history" element={<TransactionHistory />} />
        <Route path="/features" element={<AdditionalFeatures />} />
        <Route path="/notifications" element={<Notifications />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
