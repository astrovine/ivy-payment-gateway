import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { api } from '../lib/apiClient'
import Navbar from '../components/Navbar'

export default function Onboarding() {
  const { token } = useAuth()
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const [verifyForm, setVerifyForm] = useState({
    industry: '',
    staff_size: 1,
    business_name: '',
    business_type: 'Starter',
    location: '',
    phone_number: '',
    bank_account_name: '',
    bank_account_number: '',
    bank_name: '',
    business_email: ''
  })

  const [merchantForm, setMerchantForm] = useState({
    currency: 'USD',
    settlement_schedule: 'daily'
  })

  const submitVerification = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await api.verifyUser(token, {
        ...verifyForm,
        staff_size: Number(verifyForm.staff_size)
      })
      setStep(2)
    } catch (err) {
      setError(err.message || 'Verification failed')
    } finally {
      setLoading(false)
    }
  }

  const submitMerchant = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await api.createMerchant(token, merchantForm)
      navigate('/dashboard')
    } catch (err) {
      setError(err.message || 'Merchant creation failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Navbar />
      <div className="max-w-4xl mx-auto px-6 py-12">
        
        <div className="mb-12">
          <div className="flex items-center justify-center gap-4">
            <div className={`flex items-center gap-2 ${step >= 1 ? 'text-indigo-600' : 'text-slate-400'}`}>
              <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${step >= 1 ? 'bg-indigo-600 text-white' : 'bg-slate-200'}`}>
                1
              </div>
              <span className="font-medium hidden sm:block">Verify Business</span>
            </div>
            <div className={`w-16 h-1 rounded ${step >= 2 ? 'bg-indigo-600' : 'bg-slate-200'}`} />
            <div className={`flex items-center gap-2 ${step >= 2 ? 'text-indigo-600' : 'text-slate-400'}`}>
              <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${step >= 2 ? 'bg-indigo-600 text-white' : 'bg-slate-200'}`}>
                2
              </div>
              <span className="font-medium hidden sm:block">Create Account</span>
            </div>
          </div>
        </div>

        
        {step === 1 && (
          <div className="card p-8">
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-slate-900 mb-2">Verify your business</h2>
              <p className="text-slate-600">Tell us about your business to get started</p>
            </div>

            <form onSubmit={submitVerification} className="space-y-5">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Business Name *</label>
                  <input
                    required
                    value={verifyForm.business_name}
                    onChange={(e) => setVerifyForm({ ...verifyForm, business_name: e.target.value })}
                    className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Industry *</label>
                  <input
                    required
                    value={verifyForm.industry}
                    onChange={(e) => setVerifyForm({ ...verifyForm, industry: e.target.value })}
                    className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Business Type *</label>
                  <select
                    value={verifyForm.business_type}
                    onChange={(e) => setVerifyForm({ ...verifyForm, business_type: e.target.value })}
                    className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="Starter">Starter</option>
                    <option value="Registered">Registered</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Staff Size *</label>
                  <input
                    type="number"
                    min={1}
                    required
                    value={verifyForm.staff_size}
                    onChange={(e) => setVerifyForm({ ...verifyForm, staff_size: e.target.value })}
                    className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Location *</label>
                  <input
                    required
                    value={verifyForm.location}
                    onChange={(e) => setVerifyForm({ ...verifyForm, location: e.target.value })}
                    className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Phone Number *</label>
                  <input
                    required
                    value={verifyForm.phone_number}
                    onChange={(e) => setVerifyForm({ ...verifyForm, phone_number: e.target.value })}
                    className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Business Email</label>
                  <input
                    type="email"
                    value={verifyForm.business_email}
                    onChange={(e) => setVerifyForm({ ...verifyForm, business_email: e.target.value })}
                    className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Bank Account Name *</label>
                  <input
                    required
                    value={verifyForm.bank_account_name}
                    onChange={(e) => setVerifyForm({ ...verifyForm, bank_account_name: e.target.value })}
                    className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Bank Account Number *</label>
                  <input
                    required
                    value={verifyForm.bank_account_number}
                    onChange={(e) => setVerifyForm({ ...verifyForm, bank_account_number: e.target.value })}
                    className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Bank Name</label>
                  <input
                    value={verifyForm.bank_name}
                    onChange={(e) => setVerifyForm({ ...verifyForm, bank_name: e.target.value })}
                    className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>

              {error && (
                <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-3 rounded-lg transition disabled:opacity-50"
              >
                {loading ? 'Submitting...' : 'Continue'}
              </button>
            </form>
          </div>
        )}

        
        {step === 2 && (
          <div className="card p-8">
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-slate-900 mb-2">Create merchant account</h2>
              <p className="text-slate-600">Configure your payment settings</p>
            </div>

            <form onSubmit={submitMerchant} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Currency</label>
                <select
                  value={merchantForm.currency}
                  onChange={(e) => setMerchantForm({ ...merchantForm, currency: e.target.value })}
                  className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="USD">USD - US Dollar</option>
                  <option value="EUR">EUR - Euro</option>
                  <option value="GBP">GBP - British Pound</option>
                  <option value="NGN">NGN - Nigerian Naira</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Settlement Schedule</label>
                <select
                  value={merchantForm.settlement_schedule}
                  onChange={(e) => setMerchantForm({ ...merchantForm, settlement_schedule: e.target.value })}
                  className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                </select>
              </div>

              {error && (
                <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              )}

              <div className="flex gap-4">
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="flex-1 border border-slate-300 text-slate-700 font-semibold py-3 rounded-lg hover:bg-slate-50 transition"
                >
                  Back
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-3 rounded-lg transition disabled:opacity-50"
                >
                  {loading ? 'Creating...' : 'Complete Setup'}
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </>
  )
}

