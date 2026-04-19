import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../utils/api';
import { useAuthStore } from '../utils/store';
import { analyticsTracker } from '../utils/analytics';

const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const [warning, setWarning] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setWarning('');
    try {
      // Truncate password to 72 characters (bcrypt limit)
      const truncatedPassword = password.slice(0, 72);
      if (password.length > 72) setWarning('Password truncated to 72 characters before submission');

      const response = await api.login(email, truncatedPassword);
      console.log('[Login] Response:', response);
      
      // Store auth token in localStorage FIRST
      localStorage.setItem('access_token', response.access_token);
      
      // Verify it was saved
      const savedToken = localStorage.getItem('access_token');
      console.log('[Login] Token saved to localStorage:', savedToken ? `${savedToken.substring(0, 20)}...` : 'FAILED');
      
      // Then update store with token and user info
      const { setToken, setUser } = useAuthStore.getState();
      setToken(response.access_token);
      setUser({
        id: response.user_id,
        email: email,
        username: email.split('@')[0],
        tier: response.subscription_tier || 'starter',
        subscription_tier: response.subscription_tier || 'starter',
        winRate: 0,
        totalPredictions: 0,
        roi: 0,  
      });
      
      console.log('[Login] Token in store:', localStorage.getItem('access_token') ? '✓' : '✗');
      
      // Track login event
      analyticsTracker.trackLogin(response.user_id).catch(() => {});
      
      navigate('/dashboard');
    } catch (err: any) {
      console.error('[Login] Error:', err);
      // Handle Pydantic validation errors (array of error objects)
      let errorMessage = 'Login failed';
      const detail = err?.response?.data?.detail;
      if (Array.isArray(detail)) {
        // Validation error with array of errors
        errorMessage = detail.map((e: any) => e.msg || e.message).join('; ');
      } else if (typeof detail === 'string') {
        errorMessage = detail;
      } else if (err?.response?.data?.message) {
        errorMessage = err.response.data.message;
      }
      setError(errorMessage);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-100 to-purple-100">
      <div className="bg-white shadow-xl rounded-xl p-8 w-full max-w-md">
        <h2 className="text-3xl font-bold mb-6 text-center text-blue-700">Sign In</h2>
        <form onSubmit={handleSubmit} className="space-y-5">
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            required
            className="w-full px-4 py-3 border rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
            maxLength={72}
            className="w-full px-4 py-3 border rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
          {warning && <div className="text-yellow-600 text-sm text-center">{warning}</div>}
          {error && <div className="text-red-500 text-sm text-center">{error}</div>}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700 transition-all"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
          <div className="text-center">
            <Link to="/forgot-password" className="text-blue-600 hover:underline text-sm">
              Forgot password?
            </Link>
          </div>
        </form>
        <div className="mt-6 text-center text-gray-600">
          Don't have an account?{' '}
          <button className="text-blue-600 hover:underline" onClick={() => navigate('/register')}>
            Register
          </button>
        </div>
      </div>
    </div>
  );
};

export default Login;
