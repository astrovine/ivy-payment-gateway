import { useState, useEffect } from 'react'
import { api } from '../lib/apiClient'
import Navbar from '../components/Navbar'
import { Users, FileCheck, DollarSign, Activity, Search, Shield } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

export default function AdminDashboard() {
  const navigate = useNavigate()
  const [merchants, setMerchants] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    if (!user.is_superadmin) {
      navigate('/dashboard')
      return
    }
    fetchMerchants()
  }, [])

  const fetchMerchants = async () => {
    try {
      setLoading(true)
      const data = await api.adminGetMerchants(0, 100, searchTerm || null)
      setMerchants(data.merchants || [])
    } catch (err) {
      setError(err.message || 'Failed to load merchants')
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (e) => {
    e.preventDefault()
    fetchMerchants()
  }

  const getStatusColor = (status) => {
    const colors = {
      active: 'bg-green-100 text-green-700',
      suspended: 'bg-red-100 text-red-700',
      restricted: 'bg-yellow-100 text-yellow-700',
      closed: 'bg-neutral-100 text-neutral-700'
    }
    return colors[status] || 'bg-neutral-100 text-neutral-700'
  }

  const getKYCColor = (status) => {
    const colors = {
      not_started: 'bg-neutral-100 text-neutral-700',
      pending: 'bg-yellow-100 text-yellow-700',
      verified: 'bg-green-100 text-green-700',
      failed: 'bg-red-100 text-red-700'
    }
    return colors[status] || 'bg-neutral-100 text-neutral-700'
  }

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="min-h-screen bg-neutral-50 flex items-center justify-center">
          <div className="text-center">
            <div className="w-8 h-8 border-4 border-neutral-200 border-t-neutral-900 rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-neutral-600">Loading admin dashboard...</p>
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
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Shield className="w-8 h-8 text-neutral-900" />
                <div>
                  <h1 className="text-2xl font-bold text-neutral-900">Admin Dashboard</h1>
                  <p className="text-sm text-neutral-600">Platform administration</p>
                </div>
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

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6">
            <div className="flex items-center justify-between mb-2">
              <Users className="w-8 h-8 text-blue-600" />
            </div>
            <p className="text-2xl font-bold text-neutral-900">{merchants.length}</p>
            <p className="text-sm text-neutral-600">Total Merchants</p>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6">
            <div className="flex items-center justify-between mb-2">
              <FileCheck className="w-8 h-8 text-green-600" />
            </div>
            <p className="text-2xl font-bold text-neutral-900">
              {merchants.filter(m => m.kyc_status === 'verified').length}
            </p>
            <p className="text-sm text-neutral-600">KYC Verified</p>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6">
            <div className="flex items-center justify-between mb-2">
              <Activity className="w-8 h-8 text-yellow-600" />
            </div>
            <p className="text-2xl font-bold text-neutral-900">
              {merchants.filter(m => m.kyc_status === 'pending').length}
            </p>
            <p className="text-sm text-neutral-600">Pending Review</p>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6">
            <div className="flex items-center justify-between mb-2">
              <DollarSign className="w-8 h-8 text-purple-600" />
            </div>
            <p className="text-2xl font-bold text-neutral-900">
              {merchants.filter(m => m.account_status === 'active').length}
            </p>
            <p className="text-sm text-neutral-600">Active Accounts</p>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-neutral-900">Merchants</h2>
            <div className="flex gap-3">
              <button
                onClick={() => navigate('/admin/audit-logs')}
                className="px-4 py-2 text-sm font-medium text-neutral-700 bg-white border border-neutral-300 rounded-lg hover:bg-neutral-50"
              >
                Audit Logs
              </button>
              <button
                onClick={() => navigate('/admin/transactions')}
                className="px-4 py-2 text-sm font-medium text-neutral-700 bg-white border border-neutral-300 rounded-lg hover:bg-neutral-50"
              >
                Transactions
              </button>
            </div>
          </div>

          <form onSubmit={handleSearch} className="mb-6">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-neutral-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search by merchant ID, email, or name..."
                className="w-full pl-10 pr-4 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-neutral-900 focus:border-transparent"
              />
            </div>
          </form>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-neutral-200">
                  <th className="text-left py-3 px-4 text-sm font-semibold text-neutral-900">Merchant</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-neutral-900">Email</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-neutral-900">Status</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-neutral-900">KYC</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-neutral-900">Risk</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-neutral-900">Created</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-neutral-900">Actions</th>
                </tr>
              </thead>
              <tbody>
                {merchants.map((merchant) => (
                  <tr key={merchant.merchant_id} className="border-b border-neutral-100 hover:bg-neutral-50">
                    <td className="py-3 px-4">
                      <div className="font-medium text-neutral-900 text-sm">{merchant.merchant_id}</div>
                      <div className="text-xs text-neutral-600">{merchant.user_info?.name || 'N/A'}</div>
                    </td>
                    <td className="py-3 px-4 text-sm text-neutral-600">{merchant.user_info?.email || 'N/A'}</td>
                    <td className="py-3 px-4">
                      <span className={`inline-block px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(merchant.account_status)}`}>
                        {merchant.account_status}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`inline-block px-2 py-1 text-xs font-medium rounded-full ${getKYCColor(merchant.kyc_status)}`}>
                        {merchant.kyc_status}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`inline-block px-2 py-1 text-xs font-medium rounded-full ${
                        merchant.risk_level === 'low' ? 'bg-green-100 text-green-700' :
                        merchant.risk_level === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-red-100 text-red-700'
                      }`}>
                        {merchant.risk_level}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-sm text-neutral-600">
                      {merchant.created_at ? new Date(merchant.created_at).toLocaleDateString() : 'N/A'}
                    </td>
                    <td className="py-3 px-4">
                      <button
                        onClick={() => navigate(`/admin/merchants/${merchant.merchant_id}`)}
                        className="text-sm font-medium text-neutral-900 hover:underline"
                      >
                        View Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {merchants.length === 0 && (
            <div className="text-center py-12">
              <Users className="w-12 h-12 text-neutral-400 mx-auto mb-4" />
              <p className="text-neutral-600">No merchants found</p>
            </div>
          )}
        </div>
      </div>
    </div>
    </>
  )
}

