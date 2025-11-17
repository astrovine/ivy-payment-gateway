import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/apiClient'
import Navbar from '../components/Navbar'
import { ArrowLeft, Shield, DollarSign } from 'lucide-react'

export default function AdminTransactions() {
  const navigate = useNavigate()
  const [transactions, setTransactions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [merchantFilter, setMerchantFilter] = useState('')
  const [page, setPage] = useState(0)
  const [total, setTotal] = useState(0)
  const limit = 50

  useEffect(() => {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    if (!user.is_superadmin) {
      navigate('/dashboard')
      return
    }
    fetchTransactions()
  }, [page, navigate])

  const fetchTransactions = async () => {
    try {
      setLoading(true)
      const merchantId = merchantFilter || null
      const data = await api.adminGetTransactions(page * limit, limit, merchantId)
      setTransactions(data.transactions || [])
      setTotal(data.total || 0)
    } catch (err) {
      setError(err.message || 'Failed to load transactions')
    } finally {
      setLoading(false)
    }
  }

  const formatCurrency = (amount, currency = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency
    }).format(amount || 0)
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    try {
      const date = new Date(dateString)
      if (isNaN(date.getTime())) {
        return 'Invalid Date'
      }
      return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      }).format(date)
    } catch (error) {
      console.error('Date formatting error:', error, dateString)
      return 'N/A'
    }
  }

  const getStatusColor = (status) => {
    const colors = {
      succeeded: 'bg-green-100 text-green-700',
      pending: 'bg-yellow-100 text-yellow-700',
      failed: 'bg-red-100 text-red-700',
      refunded: 'bg-neutral-100 text-neutral-700'
    }
    return colors[status] || 'bg-neutral-100 text-neutral-700'
  }

  const handleFilter = (e) => {
    e.preventDefault()
    setPage(0)
    fetchTransactions()
  }

  if (loading && transactions.length === 0) {
    return (
      <>
        <Navbar />
        <div className="min-h-screen bg-neutral-50 flex items-center justify-center">
          <div className="text-center">
            <div className="w-8 h-8 border-4 border-neutral-200 border-t-neutral-900 rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-neutral-600">Loading transactions...</p>
          </div>
        </div>
      </>
    )
  }

  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-neutral-50">
        <div className="border-b border-neutral-200 bg-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <button
              onClick={() => navigate('/admin')}
              className="flex items-center gap-2 text-neutral-600 hover:text-neutral-900 mb-4"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Dashboard
            </button>
            <div className="flex items-center gap-3">
              <Shield className="w-8 h-8 text-neutral-900" />
              <div>
                <h1 className="text-2xl font-bold text-neutral-900">All Transactions</h1>
                <p className="text-sm text-neutral-600">Platform-wide payment activity</p>
              </div>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          )}

          <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6 mb-6">
            <form onSubmit={handleFilter} className="flex gap-4">
              <div className="flex-1">
                <input
                  type="text"
                  value={merchantFilter}
                  onChange={(e) => setMerchantFilter(e.target.value)}
                  placeholder="Filter by Merchant ID (e.g., merch_xxx)"
                  className="w-full px-4 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-neutral-900 focus:border-transparent"
                />
              </div>
              <button
                type="submit"
                className="px-6 py-2 bg-neutral-900 text-white rounded-lg hover:bg-neutral-800"
              >
                Filter
              </button>
              {merchantFilter && (
                <button
                  type="button"
                  onClick={() => {
                    setMerchantFilter('')
                    setPage(0)
                    setTimeout(fetchTransactions, 100)
                  }}
                  className="px-4 py-2 border border-neutral-300 rounded-lg hover:bg-neutral-50"
                >
                  Clear
                </button>
              )}
            </form>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-neutral-200">
            <div className="px-6 py-4 border-b border-neutral-200 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-neutral-900">
                Transactions ({total} total)
              </h2>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage(Math.max(0, page - 1))}
                  disabled={page === 0}
                  className="px-3 py-1 text-sm border border-neutral-300 rounded hover:bg-neutral-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage(page + 1)}
                  disabled={(page + 1) * limit >= total}
                  className="px-3 py-1 text-sm border border-neutral-300 rounded hover:bg-neutral-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-neutral-50">
                  <tr className="border-b border-neutral-200">
                    <th className="text-left py-3 px-4 text-xs font-semibold text-neutral-900 uppercase tracking-wider">Charge ID</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-neutral-900 uppercase tracking-wider">User</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-neutral-900 uppercase tracking-wider">Amount</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-neutral-900 uppercase tracking-wider">Status</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-neutral-900 uppercase tracking-wider">Description</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-neutral-900 uppercase tracking-wider">Created</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-100">
                  {transactions.map((tx) => (
                    <tr key={tx.id} className="hover:bg-neutral-50 transition-colors">
                      <td className="py-3 px-4">
                        <code className="text-xs font-mono text-neutral-900 bg-neutral-100 px-2 py-1 rounded">
                          {tx.id || 'N/A'}
                        </code>
                      </td>
                      <td className="py-3 px-4 text-sm">
                        <div className="font-medium text-neutral-900">{tx.user?.email || tx.merchant?.business_name || 'N/A'}</div>
                        <div className="text-xs text-neutral-600">{tx.user?.name || tx.merchant_id || ''}</div>
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-semibold text-neutral-900 tabular-nums">
                          {formatCurrency(tx.amount, tx.currency)}
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`inline-flex items-center px-2.5 py-1 text-xs font-medium rounded-full ${getStatusColor(tx.status)}`}>
                          {tx.status || 'unknown'}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-sm text-neutral-600 max-w-xs truncate">
                        {tx.description || tx.metadata?.description || '-'}
                      </td>
                      <td className="py-3 px-4 text-xs text-neutral-600 tabular-nums">
                        {formatDate(tx.created_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {transactions.length === 0 && !loading && (
              <div className="text-center py-12">
                <DollarSign className="w-12 h-12 text-neutral-400 mx-auto mb-4" />
                <p className="text-neutral-600 font-medium">No transactions found</p>
                <p className="text-neutral-500 text-sm mt-1">Transactions will appear here once created</p>
              </div>
            )}
          </div>

          {transactions.length > 0 && (
            <div className="mt-4 text-sm text-neutral-600 text-center">
              Showing {page * limit + 1} - {Math.min((page + 1) * limit, total)} of {total} transactions
            </div>
          )}
        </div>
      </div>
    </>
  )
}