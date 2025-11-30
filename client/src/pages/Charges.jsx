import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import { api } from '../lib/apiClient'

export default function Charges() {
  const navigate = useNavigate()
  const [charges, setCharges] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [error, setError] = useState(null)
  const [creating, setCreating] = useState(false)
  const [filter, setFilter] = useState('all')

  const [form, setForm] = useState({
    amount: '',
    currency: 'USD',
    description: ''
  })

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      navigate('/login')
      return
    }
    loadCharges()
  }, [navigate])

  const loadCharges = async () => {
    try {
      setLoading(true)
      const data = await api.getCharges()
      const chargesArray = Array.isArray(data) ? data : data?.charges || []
      setCharges(chargesArray)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const createCharge = async (e) => {
    e.preventDefault()
    setError(null)

    if (!form.amount || parseFloat(form.amount) <= 0) {
      setError('Please enter a valid amount')
      return
    }

    try {
      setCreating(true)
      const chargeData = {
        amount: Number(parseFloat(form.amount).toFixed(2)),
        currency: form.currency,
        description: form.description,
        idempotency_key: `charge-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      }

      await api.createCharge(chargeData)
      setShowCreate(false)
      setForm({ amount: '', currency: 'USD', description: '' })

      await new Promise(resolve => setTimeout(resolve, 2000))
      await loadCharges()
    } catch (err) {
      setError(err.message || 'Failed to create charge')
    } finally {
      setCreating(false)
    }
  }

  const formatCurrency = (amount, currency = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency
    }).format(parseFloat(amount) || 0)
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getStatusBadge = (status) => {
    const styles = {
      succeeded: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      pending: 'bg-amber-50 text-amber-700 border-amber-200',
      failed: 'bg-red-50 text-red-700 border-red-200'
    }
    return (
      <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${styles[status] || styles.pending}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    )
  }

  const filteredCharges = charges.filter(charge =>
    filter === 'all' ? true : charge.status === filter
  )

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="min-h-screen bg-neutral-50 flex items-center justify-center">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-neutral-900 mb-4"></div>
            <p className="text-neutral-600">Loading charges...</p>
          </div>
        </div>
      </>
    )
  }

  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-neutral-50">
        <div className="w-full px-3 sm:px-4 md:px-6 lg:max-w-7xl lg:mx-auto py-4 md:py-6 lg:py-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-neutral-900 mb-1">Charges</h1>
              <p className="text-sm md:text-base text-neutral-600">View and manage all your payment charges</p>
            </div>
            <button
              onClick={() => setShowCreate(true)}
              className="btn-primary px-4 md:px-6 py-2 md:py-3 flex items-center justify-center gap-2 text-sm md:text-base"
            >
              <svg className="w-4 h-4 md:w-5 md:h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
              </svg>
              Create Charge
            </button>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4 mb-6">
            <div className="bg-white rounded-lg p-3 md:p-4 border border-neutral-200">
              <div className="text-xs md:text-sm text-neutral-600 mb-1">Total</div>
              <div className="text-xl md:text-2xl font-bold text-neutral-900 tabular-nums lining-nums">{charges.length}</div>
            </div>
            <div className="bg-white rounded-lg p-3 md:p-4 border border-neutral-200">
              <div className="text-xs md:text-sm text-neutral-600 mb-1">Succeeded</div>
              <div className="text-xl md:text-2xl font-bold text-emerald-600 tabular-nums lining-nums">
                {charges.filter(c => c.status === 'succeeded').length}
              </div>
            </div>
            <div className="bg-white rounded-lg p-3 md:p-4 border border-neutral-200">
              <div className="text-xs md:text-sm text-neutral-600 mb-1">Pending</div>
              <div className="text-xl md:text-2xl font-bold text-amber-600 tabular-nums lining-nums">
                {charges.filter(c => c.status === 'pending').length}
              </div>
            </div>
            <div className="bg-white rounded-lg p-3 md:p-4 border border-neutral-200">
              <div className="text-xs md:text-sm text-neutral-600 mb-1">Failed</div>
              <div className="text-xl md:text-2xl font-bold text-red-600 tabular-nums lining-nums">
                {charges.filter(c => c.status === 'failed').length}
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-neutral-200 shadow-sm overflow-hidden">
            <div className="border-b border-neutral-200 overflow-x-auto">
              <div className="flex gap-1 px-4 md:px-6 py-2">
                {['all', 'succeeded', 'pending', 'failed'].map((status) => (
                  <button
                    key={status}
                    onClick={() => setFilter(status)}
                    className={`px-4 py-2 text-sm font-medium rounded-lg transition whitespace-nowrap ${
                      filter === status
                        ? 'bg-neutral-900 text-white'
                        : 'text-neutral-600 hover:bg-neutral-100'
                    }`}
                  >
                    {status.charAt(0).toUpperCase() + status.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            <div className="divide-y divide-neutral-100">
              {filteredCharges.length === 0 ? (
                <div className="px-4 md:px-6 py-12 md:py-16 text-center">
                  <div className="w-16 h-16 bg-neutral-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg className="w-8 h-8 text-neutral-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-neutral-900 mb-2">No charges found</h3>
                  <p className="text-neutral-600 mb-6">
                    {filter === 'all' ? 'Create your first charge to get started' : `No ${filter} charges yet`}
                  </p>
                  <button
                    onClick={() => setShowCreate(true)}
                    className="btn-primary px-6 py-2"
                  >
                    Create Charge
                  </button>
                </div>
              ) : (
                filteredCharges.map((charge) => (
                  <div key={charge.id} className="px-4 md:px-6 py-4 md:py-5 hover:bg-neutral-50 transition-colors">
                    <div className="flex flex-col md:flex-row md:items-center gap-3 md:gap-4">
                      <div className="flex items-start gap-3 md:gap-4 flex-1 min-w-0">
                        <div className={`w-3 h-3 rounded-full mt-1.5 flex-shrink-0 ${
                          charge.status === 'succeeded' ? 'bg-emerald-500' :
                          charge.status === 'pending' ? 'bg-amber-500' :
                          'bg-red-500'
                        }`} />
                        <div className="flex-1 min-w-0">
                          <div className="flex flex-wrap items-center gap-2 mb-1">
                            <code className="text-sm font-mono font-semibold text-neutral-900">{charge.id}</code>
                            {getStatusBadge(charge.status)}
                          </div>
                          <p className="text-sm text-neutral-700 mb-1">{charge.description || 'No description'}</p>
                          <p className="text-xs text-neutral-500">{formatDate(charge.created_at)}</p>
                        </div>
                      </div>

                      <div className="flex items-center justify-between md:justify-end gap-4 ml-6 md:ml-0">
                        <div className="text-right">
                          <div className="text-xl md:text-2xl font-bold text-neutral-900 tabular-nums lining-nums">
                            {formatCurrency(charge.amount, charge.currency)}
                          </div>
                          <div className="text-xs text-neutral-500">{charge.currency}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      {showCreate && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50 backdrop-blur-sm" onClick={() => setShowCreate(false)}>
          <div className="bg-white rounded-2xl max-w-lg w-full shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="px-6 py-5 border-b border-neutral-200">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xl font-bold text-neutral-900">Create New Charge</h3>
                  <p className="text-sm text-neutral-600 mt-1">Process a payment from your customer</p>
                </div>
                <button
                  onClick={() => setShowCreate(false)}
                  className="w-8 h-8 flex items-center justify-center rounded-lg text-neutral-400 hover:text-neutral-600 hover:bg-neutral-100 transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            {error && (
              <div className="mx-6 mt-4 p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
                <svg className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}

            <form onSubmit={createCharge} className="px-6 py-6 space-y-5">
              <div>
                <label className="block text-sm font-semibold text-neutral-700 mb-2">
                  Amount <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <div className="absolute left-4 top-1/2 -translate-y-1/2 text-neutral-500 font-medium">$</div>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    value={form.amount}
                    onChange={(e) => setForm({ ...form, amount: e.target.value })}
                    className="w-full pl-10 pr-4 py-3 border border-neutral-300 rounded-xl focus:ring-2 focus:ring-neutral-900 focus:border-neutral-900 transition-all text-lg font-semibold"
                    placeholder="100.00"
                    required
                    disabled={creating}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-neutral-700 mb-2">
                  Currency <span className="text-red-500">*</span>
                </label>
                <select
                  value={form.currency}
                  onChange={(e) => setForm({ ...form, currency: e.target.value })}
                  className="w-full px-4 py-3 border border-neutral-300 rounded-xl focus:ring-2 focus:ring-neutral-900 focus:border-neutral-900 transition-all font-medium"
                  disabled={creating}
                >
                  <option value="USD">USD - US Dollar</option>
                  <option value="EUR">EUR - Euro</option>
                  <option value="GBP">GBP - British Pound</option>
                  <option value="NGN">NGN - Nigerian Naira</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-neutral-700 mb-2">
                  Description <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  className="w-full px-4 py-3 border border-neutral-300 rounded-xl focus:ring-2 focus:ring-neutral-900 focus:border-neutral-900 transition-all resize-none"
                  placeholder="E.g., Payment for services, Product purchase"
                  rows="3"
                  required
                  disabled={creating}
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreate(false)}
                  className="flex-1 px-6 py-3 bg-white border-2 border-neutral-300 hover:border-neutral-400 hover:bg-neutral-50 text-neutral-700 rounded-xl font-semibold transition-all"
                  disabled={creating}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-6 py-3 bg-neutral-900 hover:bg-neutral-800 text-white rounded-xl font-semibold transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                  disabled={creating}
                >
                  {creating ? (
                    <>
                      <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Processing...
                    </>
                  ) : 'Create Charge'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  )
}
