import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../utils/store';
import { analyticsTracker } from '../utils/analytics';

const Header: React.FC = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { isAuthenticated, logout } = useAuthStore();

  const isActive = (path: string) => location.pathname === path;

  const handleSignIn = () => navigate('/login');
  const handleGetStarted = () => navigate('/register');
  const handleUpgrade = () => navigate('/pricing');
  const handleLogout = () => {
    // Track logout event
    const user = useAuthStore.getState().user;
    if (user?.id) {
      analyticsTracker.trackLogout(user.id);
    }
    
    logout();
    navigate('/');
  };

  return (
    <header className="fixed top-0 w-full z-50 bg-white/80 backdrop-blur-xl border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-3 flex-shrink-0 group">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-blue-600 via-purple-600 to-pink-500 flex items-center justify-center shadow-lg group-hover:shadow-xl transition-shadow">
              <span className="text-white font-bold text-lg">⚡</span>
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              SignalEdge AI
            </span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-1">
            <Link 
              to="/"
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                isActive('/') 
                  ? 'text-blue-600 bg-blue-50' 
                  : 'text-gray-600 hover:text-blue-600 hover:bg-blue-50'
              }`}
            >
              Home
            </Link>
            <Link 
              to="/dashboard"
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                isActive('/dashboard') 
                  ? 'text-blue-600 bg-blue-50' 
                  : 'text-gray-600 hover:text-blue-600 hover:bg-blue-50'
              }`}
            >
              Dashboard
            </Link>
            <Link 
              to="/pricing"
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                isActive('/pricing') 
                  ? 'text-blue-600 bg-blue-50' 
                  : 'text-gray-600 hover:text-blue-600 hover:bg-blue-50'
              }`}
            >
              Pricing
            </Link>
          </nav>

          {/* CTA Buttons */}
          <div className="hidden md:flex items-center space-x-3">
            {isAuthenticated ? (
              <>
                <button className="px-6 py-2 text-gray-700 hover:text-gray-900 font-medium transition-colors" onClick={handleUpgrade}>
                  Upgrade Package
                </button>
                <button className="px-6 py-2 bg-red-600 text-white rounded-lg font-medium hover:shadow-lg hover:-translate-y-0.5 transition-all" onClick={handleLogout}>
                  Sign Out
                </button>
              </>
            ) : (
              <>
                <button className="px-6 py-2 text-gray-700 hover:text-gray-900 font-medium transition-colors" onClick={handleSignIn}>
                  Sign In
                </button>
                <button className="px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-medium hover:shadow-lg hover:-translate-y-0.5 transition-all" onClick={handleGetStarted}>
                  Get Started
                </button>
              </>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label={mobileMenuOpen ? 'Close navigation menu' : 'Open navigation menu'}
            aria-expanded={mobileMenuOpen}
            className="md:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <svg className="w-6 h-6 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden pb-4 border-t border-gray-200">
            <Link to="/" className="block px-4 py-2 text-gray-700 hover:text-blue-600">Home</Link>
            <Link to="/dashboard" className="block px-4 py-2 text-gray-700 hover:text-blue-600">Dashboard</Link>
            <Link to="/pricing" className="block px-4 py-2 text-gray-700 hover:text-blue-600">Pricing</Link>
            {isAuthenticated ? (
              <>
                <button className="w-full mt-4 px-4 py-2 bg-gray-200 text-gray-900 rounded-lg font-medium" onClick={handleUpgrade}>
                  Upgrade Package
                </button>
                <button className="w-full mt-2 px-4 py-2 bg-red-600 text-white rounded-lg font-medium" onClick={handleLogout}>
                  Sign Out
                </button>
              </>
            ) : (
              <button className="w-full mt-4 px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-medium" onClick={handleGetStarted}>
                Get Started
              </button>
            )}
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;
