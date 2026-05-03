import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../utils/api';
import { useAuthStore } from '../utils/store';
import { analyticsTracker } from '../utils/analytics';

const Register: React.FC = () => {
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
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

      const response = await api.register(email, truncatedPassword, username);

      // Store auth token in localStorage FIRST
      localStorage.setItem('access_token', response.access_token);
      
      // Then update store with token and user info
      const { setToken, setUser } = useAuthStore.getState();
      setToken(response.access_token);
      setUser({
        id: response.user_id,
        email: email,
        username: username,
        tier: response.subscription_tier || 'starter',
        subscription_tier: response.subscription_tier || 'starter',
        winRate: 0,
        totalPredictions: 0,
        roi: 0,
      });
      
      // Track signup event
      analyticsTracker.trackSignup(email).catch(() => {});
      
      navigate('/dashboard');
    } catch (err: any) {
      console.error('[Register] Error:', err);
      // Handle Pydantic validation errors (array of error objects)
      let errorMessage = 'Registration failed';
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
        <h2 className="text-3xl font-bold mb-6 text-center text-blue-700">Create Your Account</h2>
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
            type="text"
            placeholder="Username"
            value={username}
            onChange={e => setUsername(e.target.value)}
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
            {loading ? 'Registering...' : 'Register'}
          </button>
        </form>
        <div className="mt-6 text-center text-gray-600">
          Already have an account?{' '}
          <button className="text-blue-600 hover:underline" onClick={() => navigate('/login')}>
            Sign In
          </button>
        </div>
      </div>
    </div>
  );
};

export default Register;
