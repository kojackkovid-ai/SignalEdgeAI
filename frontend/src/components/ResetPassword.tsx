import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import '../styles/auth.css';

const ResetPassword: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [tokenValid, setTokenValid] = useState(true);
  const navigate = useNavigate();

  const token = searchParams.get('token');

  useEffect(() => {
    if (!token) {
      setTokenValid(false);
      setError('Invalid or missing reset token. Please request a new password reset.');
    }
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Validate passwords match
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    // Validate password strength
    if (newPassword.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('/api/auth/reset-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          token,
          new_password: newPassword,
        }),
      });

      if (response.ok) {
        setSuccess(true);
        setNewPassword('');
        setConfirmPassword('');
        // Redirect to login after a delay
        setTimeout(() => {
          navigate('/login');
        }, 2000);
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to reset password. Please try again or request a new reset link.');
        setTokenValid(false);
      }
    } catch (err) {
      setError('Network error. Please check your connection and try again.');
      console.error('Reset password error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="auth-container">
        <div className="auth-card">
          <div className="success-message">
            <h2>Password Reset Successfully</h2>
            <p>Your password has been reset successfully.</p>
            <p>You can now log in with your new password.</p>
            <Link to="/login" className="btn btn-primary" style={{ marginTop: '20px' }}>
              Go to Login
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (!tokenValid) {
    return (
      <div className="auth-container">
        <div className="auth-card">
          <div className="error-section">
            <h2>Invalid Reset Link</h2>
            <p>{error}</p>
            <Link to="/forgot-password" className="btn btn-primary" style={{ marginTop: '20px' }}>
              Request New Reset Link
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>Reset Your Password</h2>
        <p className="auth-description">
          Enter your new password below. Make sure it's strong and unique.
        </p>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="newPassword">New Password</label>
            <input
              type="password"
              id="newPassword"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="••••••"
              required
              disabled={loading}
              autoComplete="new-password"
              minLength={6}
            />
            <small>At least 6 characters</small>
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <input
              type="password"
              id="confirmPassword"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="••••••"
              required
              disabled={loading}
              autoComplete="new-password"
              minLength={6}
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-block"
            disabled={loading}
          >
            {loading ? 'Resetting Password...' : 'Reset Password'}
          </button>
        </form>

        <div className="auth-links">
          <Link to="/login">Back to Login</Link>
          <Link to="/register">Create Account</Link>
        </div>
      </div>
    </div>
  );
};

export default ResetPassword;
