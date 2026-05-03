import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import ErrorBoundary from './components/ErrorBoundary';
import Header from './components/Header';
import Footer from './components/Footer';
import Dashboard from './pages/Dashboard';
import Analytics from './pages/Analytics';
import AdminDashboard from './pages/AdminDashboard';
import Pricing from './pages/Pricing';
import Payment from './pages/Payment';
import LandingPage from './pages/LandingPage';
import Register from './pages/Register';
import Login from './pages/Login';
import ForgotPassword from './components/ForgotPassword';
import ResetPassword from './components/ResetPassword';
import TermsOfService from './pages/TermsOfService';
import PrivacyPolicy from './pages/PrivacyPolicy';
import ResponsibleGambling from './pages/ResponsibleGambling';
import RefundPolicy from './pages/RefundPolicy';
import CookiePolicy from './pages/CookiePolicy';
import RiskDisclosure from './pages/RiskDisclosure';
import { tokenManager } from './utils/tokenManager';
import './styles/theme.css';

const App: React.FC = () => {
  // Initialize token monitoring on app load
  useEffect(() => {
    // Start monitoring token expiration
    tokenManager.startMonitoring(
      // On token expired — preserve current location so user returns after re-login
      () => {
        const current = window.location.pathname + window.location.search;
        const shouldPreserve = current !== '/' && current !== '/login' && current !== '/register';
        window.location.href = shouldPreserve
          ? `/login?redirect=${encodeURIComponent(current)}`
          : '/login';
      },
      // On token refreshed
      (_newToken) => {}
    );

    // Cleanup on unmount
    return () => {
      tokenManager.stopMonitoring();
    };
  }, []);

  return (
    <ErrorBoundary>
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <div className="flex flex-col min-h-screen">
          <Header />
          <main className="flex-1">
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/admin" element={<AdminDashboard />} />
              <Route path="/pricing" element={<Pricing />} />
              <Route path="/payment" element={<Payment />} />
              <Route path="/register" element={<Register />} />
              <Route path="/login" element={<Login />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />
              <Route path="/reset-password" element={<ResetPassword />} />
              {/* Legal Pages */}
              <Route path="/legal/terms" element={<TermsOfService />} />
              <Route path="/legal/privacy" element={<PrivacyPolicy />} />
              <Route path="/legal/responsible-gambling" element={<ResponsibleGambling />} />
              <Route path="/legal/refund" element={<RefundPolicy />} />
              <Route path="/legal/cookies" element={<CookiePolicy />} />
              <Route path="/legal/risk" element={<RiskDisclosure />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
          <Footer />
        </div>
      </BrowserRouter>
    </ErrorBoundary>
  );
};

export default App;

