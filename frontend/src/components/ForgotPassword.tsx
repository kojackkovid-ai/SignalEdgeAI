import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import '../styles/auth.css';

interface ForgotPasswordProps {
  onBack?: () => void;
}

const ForgotPassword: React.FC<ForgotPasswordProps> = ({ onBack }) => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch('/api/auth/forgot-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      if (response.ok) {
        setSuccess(true);
        setEmail('');
        // Optionally navigate after a delay
        setTimeout(() => {
          navigate('/login');
        }, 3000);
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to send reset email. Please try again.');
      }
    } catch (err) {
      setError('Network error. Please check your connection and try again.');
      console.error('Forgot password error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="auth-container">
        <div className="auth-card">
          <div className="success-message">
            <h2>Check Your Email</h2>
            <p>
              If an account exists for <strong>{email}</strong>, you'll receive a password reset link within a few minutes.
            </p>
            <p>Please check your email and follow the link to reset your password.</p>
            <p className="text-muted">Link expires in 1 hour for security.</p>
            <Link to="/login" className="btn btn-primary" style={{ marginTop: '20px' }}>
              Back to Login
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>Forgot Password</h2>
        <p className="auth-description">
          Enter your email address and we'll send you a link to reset your password.
        </p>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your@email.com"
              required
              disabled={loading}
              autoComplete="email"
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-block"
            disabled={loading}
          >
            {loading ? 'Sending...' : 'Send Reset Link'}
          </button>
        </form>

        <div className="auth-links">
          <Link to="/login">Back to Login</Link>
          <Link to="/register">Create Account</Link>
        </div>

        {onBack && (
          <button onClick={onBack} className="btn btn-text">
            ← Go Back
          </button>
        )}
      </div>
    </div>
  );
};

export default ForgotPassword;
