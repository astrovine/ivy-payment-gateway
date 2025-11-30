import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import './index.css'
import './custom.css'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import LandingPage from './pages/LandingPage'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Onboarding from './pages/Onboarding'
import Charges from './pages/Charges'
import APIKeys from './pages/APIKeys'
import Settings from './pages/Settings'
import Analytics from './pages/Analytics'
import VerifyAccount from './pages/VerifyAccount'
import CreateMerchantAccount from './pages/CreateMerchantAccount'
import KYC from './pages/KYC'
import AdminDashboard from './pages/AdminDashboard'
import AdminMerchantDetails from './pages/AdminMerchantDetails'
import AdminAuditLogs from './pages/AdminAuditLogs'
import AdminTransactions from './pages/AdminTransactions'
import AdminPayouts from './pages/AdminPayouts'
import OnboardingGuard from './components/OnboardingGuard'
import Payouts from './pages/Payouts'
import Notifications from './pages/Notifications'
import AuthCallback from './pages/AuthCallback'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          <Route path="/auth/callback" element={<AuthCallback />} />

          <Route path="/onboarding" element={<ProtectedRoute><Onboarding /></ProtectedRoute>} />
          <Route path="/onboarding/verify" element={<ProtectedRoute><VerifyAccount /></ProtectedRoute>} />
          <Route path="/onboarding/merchant" element={<ProtectedRoute><CreateMerchantAccount /></ProtectedRoute>} />
          <Route path="/dashboard" element={<ProtectedRoute><OnboardingGuard><Dashboard /></OnboardingGuard></ProtectedRoute>} />
          <Route path="/analytics" element={<ProtectedRoute><OnboardingGuard><Analytics /></OnboardingGuard></ProtectedRoute>} />
          <Route path="/charges" element={<ProtectedRoute><OnboardingGuard><Charges /></OnboardingGuard></ProtectedRoute>} />
          <Route path="/api-keys" element={<ProtectedRoute><OnboardingGuard><APIKeys /></OnboardingGuard></ProtectedRoute>} />
          <Route path="/kyc" element={<ProtectedRoute><OnboardingGuard><KYC /></OnboardingGuard></ProtectedRoute>} />
          <Route path="/settings" element={<ProtectedRoute><OnboardingGuard><Settings /></OnboardingGuard></ProtectedRoute>} />
          <Route path="/admin" element={<ProtectedRoute><AdminDashboard /></ProtectedRoute>} />
          <Route path="/admin/merchants/:merchantId" element={<ProtectedRoute><AdminMerchantDetails /></ProtectedRoute>} />
          <Route path="/admin/audit-logs" element={<ProtectedRoute><AdminAuditLogs /></ProtectedRoute>} />
          <Route path="/admin/transactions" element={<ProtectedRoute><AdminTransactions /></ProtectedRoute>} />
          <Route path="/admin/payouts" element={<ProtectedRoute><AdminPayouts /></ProtectedRoute>} />
          <Route path="/payouts" element={<ProtectedRoute><OnboardingGuard><Payouts /></OnboardingGuard></ProtectedRoute>} />
          <Route path="/notifications" element={<ProtectedRoute><OnboardingGuard><Notifications /></OnboardingGuard></ProtectedRoute>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  </StrictMode>,
)