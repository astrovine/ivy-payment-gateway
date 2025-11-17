import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/apiClient'
import Navbar from '../components/Navbar'
import { ArrowLeft, Shield, Filter } from 'lucide-react'

export default function AdminAuditLogs() {
  const navigate = useNavigate()
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [filters, setFilters] = useState({
    user_id: '',
    action: ''
  })
  const [page, setPage] = useState(0)
  const [total, setTotal] = useState(0)
  const limit = 50

  useEffect(() => {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    if (!user.is_superadmin) {
      navigate('/dashboard')
      return
    }
    fetchLogs()
  }, [page])

  const fetchLogs = async () => {
    try {
      setLoading(true)
      const userId = filters.user_id ? parseInt(filters.user_id) : null
      const action = filters.action || null
      const data = await api.adminGetAuditLogs(page * limit, limit, userId, action)
      setLogs(data.logs || [])
      setTotal(data.total || 0)
    } catch (err) {
      setError(err.message || 'Failed to load audit logs')
    } finally {
      setLoading(false)
    }
  }

  const handleFilter = (e) => {
    e.preventDefault()
    setPage(0)
    fetchLogs()
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    const date = new Date(dateString)
    return date.toLocaleString()
  }

  const getActionColor = (action) => {
    if (!action || typeof action !== 'string') return 'bg-neutral-100 text-neutral-700'

    if (action.includes('FAILED') || action.includes('REJECTED') || action.includes('DELETE')) {
      return 'bg-red-100 text-red-700'
    }
    if (action.includes('APPROVED') || action.includes('SUCCESS') || action.includes('CREATED')) {
      return 'bg-green-100 text-green-700'
    }
    if (action.includes('UPDATED') || action.includes('MODIFIED')) {
      return 'bg-blue-100 text-blue-700'
    }
    return 'bg-neutral-100 text-neutral-700'
  }

  if (loading && logs.length === 0) {
    return (
      <>
        <Navbar />
        <div className="min-h-screen bg-neutral-50 flex items-center justify-center">
          <div className="text-center">
            <div className="w-8 h-8 border-4 border-neutral-200 border-t-neutral-900 rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-neutral-600">Loading audit logs...</p>
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
                <h1 className="text-2xl font-bold text-neutral-900">Audit Logs</h1>
                <p className="text-sm text-neutral-600">Security and compliance audit trail</p>
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
                value={filters.user_id}
                onChange={(e) => setFilters({ ...filters, user_id: e.target.value })}
                placeholder="User ID"
                className="w-full px-4 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-neutral-900 focus:border-transparent"
              />
            </div>
            <div className="flex-1">
              <input
                type="text"
                value={filters.action}
                onChange={(e) => setFilters({ ...filters, action: e.target.value })}
                placeholder="Action (e.g., LOGIN, CHARGE_CREATED)"
                className="w-full px-4 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-neutral-900 focus:border-transparent"
              />
            </div>
            <button
              type="submit"
              className="px-6 py-2 bg-neutral-900 text-white rounded-lg hover:bg-neutral-800 flex items-center gap-2"
            >
              <Filter className="w-4 h-4" />
              Filter
            </button>
          </form>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-neutral-200">
          <div className="px-6 py-4 border-b border-neutral-200 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-neutral-900">
              Audit Trail ({total} total)
            </h2>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(Math.max(0, page - 1))}
                disabled={page === 0}
                className="px-3 py-1 text-sm border border-neutral-300 rounded hover:bg-neutral-50 disabled:opacity-50"
              >
                Previous
              </button>
              <button
                onClick={() => setPage(page + 1)}
                disabled={(page + 1) * limit >= total}
                className="px-3 py-1 text-sm border border-neutral-300 rounded hover:bg-neutral-50 disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-neutral-50">
                <tr className="border-b border-neutral-200">
                  <th className="text-left py-3 px-4 text-xs font-semibold text-neutral-900">Timestamp</th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-neutral-900">User</th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-neutral-900">Action</th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-neutral-900">Resource</th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-neutral-900">IP Address</th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-neutral-900">Details</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id} className="border-b border-neutral-100 hover:bg-neutral-50">
                    <td className="py-3 px-4 text-xs text-neutral-600">
                      {formatDate(log.created_at)}
                    </td>
                    <td className="py-3 px-4 text-sm">
                      <div className="font-medium text-neutral-900">User #{log.user_id || 'N/A'}</div>
                      {log.merchant_id && (
                        <div className="text-xs text-neutral-600">{log.merchant_id}</div>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`inline-block px-2 py-1 text-xs font-medium rounded-full ${getActionColor(log.action)}`}>
                        {log.action}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-sm text-neutral-600">
                      <div>{log.resource_type}</div>
                      {log.resource_id && (
                        <div className="text-xs text-neutral-500">{log.resource_id}</div>
                      )}
                    </td>
                    <td className="py-3 px-4 text-xs font-mono text-neutral-600">
                      {log.ip_address || 'N/A'}
                    </td>
                    <td className="py-3 px-4 text-xs text-neutral-600 max-w-xs truncate">
                      {log.extra_data || log.changes || '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {logs.length === 0 && (
            <div className="text-center py-12">
              <Shield className="w-12 h-12 text-neutral-400 mx-auto mb-4" />
              <p className="text-neutral-600">No audit logs found</p>
            </div>
          )}
        </div>

        <div className="mt-4 text-sm text-neutral-600 text-center">
          Showing {page * limit + 1} - {Math.min((page + 1) * limit, total)} of {total} logs
        </div>
      </div>
    </div>
    </>
  )
}

