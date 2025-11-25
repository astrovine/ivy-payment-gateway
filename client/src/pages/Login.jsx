import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../lib/apiClient'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const [formData, setFormData] = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [focusedField, setFocusedField] = useState(null)

  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      localStorage.removeItem('token')
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')

      const data = await api.login(formData.email, formData.password)

      login(data)

      const userToCheck = data.user

      if (userToCheck.is_superadmin) {
        navigate('/admin', { replace: true })
      } else if (userToCheck.onboarding_stage === 'account_created') {
        navigate('/onboarding/verify', { replace: true })
      } else if (userToCheck.onboarding_stage === 'verified') {
        navigate('/onboarding/merchant', { replace: true })
      } else {
        navigate('/dashboard', { replace: true })
      }
    } catch (err) {
      let errorMessage = err.message
      if (err.status === 401) {
        errorMessage = 'Incorrect email or password. Please check your credentials and try again.'
      } else if (err.status === 500) {
        errorMessage = 'Server error. Please try again later.'
      } else if (err.status === 0 || !err.status) {
        errorMessage = 'Unable to connect to server. Please check your internet connection.'
      } else if (!errorMessage) {
        errorMessage = 'An unexpected error occurred. Please try again.'
      }
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleLogin = () => {
    window.location.href = "http://ivypayments.ddns.net:8000/api/v1/auth/google/login";
  };

  const handleGitHubLogin = () => {
    window.location.href = "http://ivypayments.ddns.net:8000/api/v1/auth/github/login";
  };
  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 via-white to-blue-50/30 flex flex-col px-4 py-6">

      <header className="w-full max-w-6xl mx-auto mb-8">
        <Link
          to="/"
          className="inline-flex items-center gap-2.5 text-neutral-900 hover:opacity-70 transition-opacity"
        >
          <div className="w-9 h-9 bg-neutral-900 rounded-lg flex items-center justify-center shadow-sm">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707" />
            </svg>
          </div>
          <span className="text-xl font-semibold">Ivy</span>
        </Link>
      </header>


      <div className="flex-1 flex items-center justify-center">
        <div className="w-full max-w-[440px]">

          <div className="bg-white border border-neutral-200 rounded-2xl p-8 md:p-10 shadow-xl shadow-neutral-200/50">

            <div className="mb-8">
              <h1 className="text-3xl md:text-4xl font-semibold text-neutral-900 mb-2 tracking-tight">
                Welcome back
              </h1>
              <p className="text-base text-neutral-600 tracking-[-0.01em]">
                Sign in to access your account
              </p>
            </div>


            {error && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl">
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                  <p className="text-sm text-red-800 font-medium">{error}</p>
                </div>
              </div>
            )}


            <form onSubmit={handleSubmit} className="space-y-5">

              <div>
                <label
                  htmlFor="email"
                  className="block text-sm font-semibold text-neutral-700 mb-2.5 tracking-[-0.01em]"
                >
                  Email address
                </label>
                <input
                  id="email"
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  onFocus={() => setFocusedField('email')}
                  onBlur={() => setFocusedField(null)}
                  className={`w-full px-4 py-3.5 bg-white border-2 rounded-xl text-neutral-900 text-[15px] placeholder-neutral-400 focus:outline-none transition-all tracking-[-0.01em] ${
                    focusedField === 'email' ? 'border-neutral-900 shadow-md shadow-neutral-900/5' : 'border-neutral-200 hover:border-neutral-300'
                  }`}
                  placeholder="you@company.com"
                />
              </div>


              <div>
                <div className="flex items-center justify-between mb-2.5">
                  <label
                    htmlFor="password"
                    className="block text-sm font-semibold text-neutral-700 tracking-[-0.01em]"
                  >
                    Password
                  </label>
                  <a
                    href="#"
                    className="text-xs font-semibold text-neutral-600 hover:text-neutral-900 transition-colors tracking-[-0.01em]"
                  >
                    Forgot password?
                  </a>
                </div>
                <input
                  id="password"
                  type="password"
                  required
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  onFocus={() => setFocusedField('password')}
                  onBlur={() => setFocusedField(null)}
                  className={`w-full px-4 py-3.5 bg-white border-2 rounded-xl text-neutral-900 text-[15px] placeholder-neutral-400 focus:outline-none transition-all tracking-[-0.01em] ${
                    focusedField === 'password' ? 'border-neutral-900 shadow-md shadow-neutral-900/5' : 'border-neutral-200 hover:border-neutral-300'
                  }`}
                  placeholder="Enter your password"
                />
              </div>


              <div className="pt-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3.5 bg-neutral-900 hover:bg-neutral-800 active:bg-black text-white text-[15px] font-semibold rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-lg shadow-neutral-900/15 hover:shadow-xl hover:shadow-neutral-900/20 tracking-[-0.01em]"
                >
                  {loading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      <span>Signing in...</span>
                    </>
                  ) : (
                    <>
                      <span>Sign in</span>
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                      </svg>
                    </>
                  )}
                </button>
              </div>
            </form>


            <div className="relative my-7">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-neutral-200"></div>
              </div>
              <div className="relative flex justify-center text-xs">
                <span className="px-3 bg-white text-neutral-500 font-medium">Or continue with</span>
              </div>
            </div>


            <div className="grid grid-cols-2 gap-3">

              <button
                type="button"
                onClick={handleGoogleLogin}
                className="py-2.5 px-4 bg-white hover:bg-neutral-50 border-2 border-neutral-200 hover:border-neutral-300 text-neutral-700 text-sm font-medium rounded-xl transition-all flex items-center justify-center gap-2.5"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                <span>Google</span>
              </button>


              <button
                type="button"
                onClick={handleGitHubLogin}
                className="py-2.5 px-4 bg-white hover:bg-neutral-50 border-2 border-neutral-200 hover:border-neutral-300 text-neutral-700 text-sm font-medium rounded-xl transition-all flex items-center justify-center gap-2.5"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                  <path fillRule="evenodd" d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12" clipRule="evenodd" />
                </svg>
                <span>GitHub</span>
              </button>
            </div>


            <button
              type="button"
              className="w-full mt-3 py-2.5 px-4 bg-neutral-50 hover:bg-neutral-100 border-2 border-neutral-200 hover:border-neutral-300 text-neutral-700 text-sm font-medium rounded-xl transition-all flex items-center justify-center gap-2.5"
            >
              <svg className="w-5 h-5 text-neutral-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
              </svg>
              <span>Sign in with Security Key</span>
            </button>
          </div>


          <div className="mt-6 text-center">
            <span className="text-sm text-neutral-600">New to Ivy? </span>
            <Link
              to="/register"
              className="text-sm font-semibold text-neutral-900 hover:text-neutral-700 transition-colors"
            >
              Create an account
            </Link>
          </div>
        </div>
      </div>


      <footer className="w-full max-w-6xl mx-auto mt-8">
        <div className="flex flex-col items-center gap-4">

          <div className="max-w-2xl text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-neutral-50 border border-neutral-200 rounded-full">
              <svg className="w-4 h-4 text-neutral-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              <p className="text-xs text-neutral-600">
                <span className="font-semibold">Secure access:</span> Add multiple authentication methods like Security Key and Touch ID for enhanced account protection
              </p>
            </div>
          </div>


          <div className="flex items-center gap-4 text-xs text-neutral-500">
            <a href="#" className="hover:text-neutral-900 transition-colors font-medium">Help Center</a>
            <span>•</span>
            <a href="#" className="hover:text-neutral-900 transition-colors font-medium">Privacy Policy</a>
            <span>•</span>
            <a href="#" className="hover:text-neutral-900 transition-colors font-medium">Terms of Service</a>
            <span>•</span>
            <a href="#" className="hover:text-neutral-900 transition-colors font-medium">Status</a>
          </div>
        </div>
      </footer>
    </div>
  )
}