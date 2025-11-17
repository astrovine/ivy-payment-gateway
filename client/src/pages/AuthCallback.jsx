import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../lib/apiClient';

const FullPageSpinner = () => (
  <div className="flex items-center justify-center h-screen bg-neutral-50">
    <div className="w-12 h-12 border-4 border-neutral-200 border-t-neutral-900 rounded-full animate-spin" />
    <p className="ml-4 text-neutral-600">Welcome...</p>
  </div>
);

export default function AuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { login, logout } = useAuth();
  const [error, setError] = useState(null);
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    if (processing) return;

    const processAuth = async () => {
      setProcessing(true);

      const access_token = searchParams.get('access_token');
      const refresh_token = searchParams.get('refresh_token');

      if (!access_token) {
        setError('Authentication failed. No token provided.');
        setTimeout(() => navigate('/login'), 2000);
        return;
      }

      localStorage.setItem('access_token', access_token);
      if (refresh_token) {
        localStorage.setItem('refresh_token', refresh_token);
      }

      try {
        const user = await api.getCurrentUser();

        localStorage.setItem('user', JSON.stringify(user));

        // Call the login function from context
        login({
          access_token: access_token,
          refresh_token: refresh_token,
          user: user
        });

        // Navigate based on user state
        if (user.is_superadmin) {
          navigate('/admin', { replace: true });
        } else if (user.onboarding_stage === 'account_created') {
          navigate('/onboarding/verify', { replace: true });
        } else if (user.onboarding_stage === 'verified') {
          navigate('/onboarding/merchant', { replace: true });
        } else {
          navigate('/dashboard', { replace: true });
        }

      } catch (err) {
        console.error('Auth callback error:', err);
        setError('Failed to fetch user data after login.');
        logout();
        setTimeout(() => navigate('/login', { replace: true }), 2000);
      }
    };

    processAuth();
  }, [searchParams, navigate, login, logout, processing]); // Include all dependencies

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-red-50">
        <div className="max-w-md p-8 bg-white rounded-xl shadow-lg border border-red-200">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
              <svg className="w-6 h-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-semibold text-red-900">Authentication Error</h2>
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
          <a
            href="/login"
            className="block w-full text-center px-4 py-2 bg-neutral-900 text-white rounded-lg hover:bg-neutral-800 transition-colors"
          >
            Return to Login
          </a>
        </div>
      </div>
    );
  }

  return <FullPageSpinner />;
}
