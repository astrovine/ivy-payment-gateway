import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/apiClient'
import { useAuth } from '../context/AuthContext'
import Navbar from '../components/Navbar'

export default function CreateMerchantAccount() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const { token, login } = useAuth()

  const [form, setForm] = useState({
    currency: 'USD',
    settlement_schedule: 'daily'
  })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await api.createMerchant(token, form)
      const user = await api.getCurrentUser()
      login({
        access_token: token,
        refresh_token: localStorage.getItem('refresh_token'),
        user: user
      });

      navigate('/dashboard', {
        replace: true,
        state: { message: 'Merchant account created! Welcome to your dashboard.' }
      });

    } catch (err) {
      setError(err.message || 'Failed to create merchant account')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Navbar />

      <div className="min-h-screen bg-neutral-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full">
          <div className="text-center mb-8">
            <div className="mx-auto w-16 h-16 bg-neutral-900 rounded-2xl flex items-center justify-center mb-4">
              <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
            <h1 className="text-3xl font-bold text-neutral-900 mb-2">Create Merchant Account</h1>
            <p className="text-neutral-600">Set up your merchant account to start accepting payments</p>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
              <svg className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-sm border border-neutral-200 p-8 space-y-6">
            <div>
              <label className="block text-sm font-semibold text-neutral-700 mb-2">
                Default Currency <span className="text-red-500">*</span>
              </label>
              <select
                value={form.currency}
                onChange={(e) => setForm({ ...form, currency: e.target.value })}
                className="w-full px-4 py-3 border border-neutral-300 rounded-xl focus:ring-2 focus:ring-neutral-900 focus:border-neutral-900 transition-all font-medium"
                required
                disabled={loading}
              >
                <option value="USD">USD - US Dollar</option>
                <option value="EUR">EUR - Euro</option>
                <option value="GBP">GBP - British Pound</option>
                <option value="NGN">NGN - Nigerian Naira</option>
              </select>
              <p className="mt-2 text-xs text-neutral-500">
                This will be your default currency for transactions
              </p>
            </div>

            <div>
              <label className="block text-sm font-semibold text-neutral-700 mb-2">
                Settlement Schedule <span className="text-red-500">*</span>
              </label>
              <select
                value={form.settlement_schedule}
                onChange={(e) => setForm({ ...form, settlement_schedule: e.target.value })}
                className="w-full px-4 py-3 border border-neutral-300 rounded-xl focus:ring-2 focus:ring-neutral-900 focus:border-neutral-900 transition-all font-medium"
                required
                disabled={loading}
              >
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
              </select>
              <p className="mt-2 text-xs text-neutral-500">
                How often you'd like to receive payouts
              </p>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
              <div className="flex gap-3">
                <svg className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
                <div>
                  <h3 className="text-sm font-semibold text-blue-900 mb-1">What's next?</h3>
                  <p className="text-xs text-blue-800">
                    After creating your merchant account, you'll be able to create API keys and start processing payments.
                  </p>
                </div>
              </div>
            </div>

            <div className="flex gap-4 pt-4">
              <button
                type="button"
                onClick={() => navigate('/login')}
                className="flex-1 px-6 py-3 bg-white border-2 border-neutral-300 hover:border-neutral-400 hover:bg-neutral-50 text-neutral-700 rounded-xl font-semibold transition-all"
                disabled={loading}
              >
                Back
              </button>
              <button
                type="submit"
                className="flex-1 px-6 py-3 bg-neutral-900 hover:bg-neutral-800 text-white rounded-xl font-semibold transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Creating...
                  </>
                ) : 'Create Account'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </>
  )
}