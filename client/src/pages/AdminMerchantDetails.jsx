import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../lib/apiClient'
import Navbar from '../components/Navbar'
import { ArrowLeft, CheckCircle, XCircle, AlertTriangle, Shield } from 'lucide-react'

export default function AdminMerchantDetails() {
  const { merchantId } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [actionLoading, setActionLoading] = useState(false)

  const [showStatusModal, setShowStatusModal] = useState(false)
  const [showKYCModal, setShowKYCModal] = useState(false)
  const [showRiskModal, setShowRiskModal] = useState(false)

  const [newStatus, setNewStatus] = useState('')
  const [rejectionReason, setRejectionReason] = useState('')
  const [riskData, setRiskData] = useState({
    risk_level: 'low',
    risk_factors: [],
    review_required: false,
    notes: ''
  })

  useEffect(() => {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    if (!user.is_superadmin) {
      navigate('/dashboard')
      return
    }
    fetchMerchantDetails()
  }, [merchantId])

  const fetchMerchantDetails = async () => {
    try {
      setLoading(true)
      const merchantData = await api.adminGetMerchantDetails(merchantId)
      console.log('Merchant Data:', merchantData)
      console.log('User:', merchantData?.user)
      console.log('KYC Status:', merchantData?.kyc_status)
      setData(merchantData)
      setNewStatus(merchantData.merchant.account_status)
      setRiskData({
        risk_level: merchantData.merchant.risk_level,
        risk_factors: [],
        review_required: false,
        notes: ''
      })
    } catch (err) {
      console.error('Fetch Error:', err)
      setError(err.message || 'Failed to load merchant details')
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateStatus = async () => {
    try {
      setActionLoading(true)
      setError('')
      await api.adminUpdateMerchantStatus(merchantId, newStatus)
      setSuccess('Merchant status updated successfully')
      setShowStatusModal(false)
      await fetchMerchantDetails()
    } catch (err) {
      setError(err.message || 'Failed to update status')
    } finally {
      setActionLoading(false)
    }
  }

  const handleApproveKYC = async () => {
    if (!data?.user?.id) {
      setError('User ID not found. Cannot approve KYC.')
      return
    }
    try {
      setActionLoading(true)
      setError('')
      await api.adminApproveKYC(data.user.id)
      setSuccess('KYC approved successfully')
      setShowKYCModal(false)
      await fetchMerchantDetails()
    } catch (err) {
      setError(err.message || 'Failed to approve KYC')
    } finally {
      setActionLoading(false)
    }
  }

  const handleRejectKYC = async () => {
    if (!data?.user?.id) {
      setError('User ID not found. Cannot reject KYC.')
      return
    }
    if (!rejectionReason.trim()) {
      setError('Please provide a rejection reason')
      return
    }
    try {
      setActionLoading(true)
      setError('')
      await api.adminRejectKYC(data.user.id, rejectionReason)
      setSuccess('KYC rejected')
      setShowKYCModal(false)
      setRejectionReason('')
      await fetchMerchantDetails()
    } catch (err) {
      setError(err.message || 'Failed to reject KYC')
    } finally {
      setActionLoading(false)
    }
  }

  const handleUpdateRisk = async () => {
    try {
      setActionLoading(true)
      setError('')
      await api.adminUpdateRiskAssessment(merchantId, riskData)
      setSuccess('Risk assessment updated successfully')
      setShowRiskModal(false)
      await fetchMerchantDetails()
    } catch (err) {
      setError(err.message || 'Failed to update risk assessment')
    } finally {
      setActionLoading(false)
    }
  }

  const handleSyncBalances = async () => {
    try {
      setActionLoading(true)
      setError('')
      await api.adminSyncBalances(merchantId)
      setSuccess('Balances synced successfully')
      await fetchMerchantDetails()
    } catch (err) {
      setError(err.message || 'Failed to sync balances')
    } finally {
      setActionLoading(false)
    }
  }

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="min-h-screen bg-neutral-50 flex items-center justify-center">
          <div className="text-center">
            <div className="w-8 h-8 border-4 border-neutral-200 border-t-neutral-900 rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-neutral-600">Loading merchant details...</p>
          </div>
        </div>
      </>
    )
  }

  if (!data) {
    return (
      <>
        <Navbar />
        <div className="min-h-screen bg-neutral-50 flex items-center justify-center">
          <p className="text-neutral-600">Merchant not found</p>
        </div>
      </>
    )
  }

  const merchant = data.merchant
  const user = data.user
  const verifiedInfo = data.verified_info
  const kycStatus = data.kyc_status
  const kycDocuments = data.kyc_documents || []

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
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Shield className="w-8 h-8 text-neutral-900" />
              <div>
                <h1 className="text-2xl font-bold text-neutral-900">Merchant Details</h1>
                <p className="text-sm text-neutral-600">{merchant.merchant_id}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5" />
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        )}

        {success && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
            <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
            <p className="text-green-700 text-sm">{success}</p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-neutral-900">Account Information</h2>
                <button
                  onClick={() => setShowStatusModal(true)}
                  className="px-4 py-2 text-sm font-medium text-neutral-700 bg-white border border-neutral-300 rounded-lg hover:bg-neutral-50"
                >
                  Update Status
                </button>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-neutral-600 mb-1">Email</p>
                  <p className="text-neutral-900 font-medium">{user.email}</p>
                </div>
                <div>
                  <p className="text-neutral-600 mb-1">Name</p>
                  <p className="text-neutral-900 font-medium">{user.name}</p>
                </div>
                <div>
                  <p className="text-neutral-600 mb-1">Account Status</p>
                  <span className={`inline-block px-2 py-1 text-xs font-medium rounded-full ${
                    merchant.account_status === 'active' ? 'bg-green-100 text-green-700' :
                    merchant.account_status === 'suspended' ? 'bg-red-100 text-red-700' :
                    'bg-yellow-100 text-yellow-700'
                  }`}>
                    {merchant.account_status}
                  </span>
                </div>
                <div>
                  <p className="text-neutral-600 mb-1">Risk Level</p>
                  <span className={`inline-block px-2 py-1 text-xs font-medium rounded-full ${
                    merchant.risk_level === 'low' ? 'bg-green-100 text-green-700' :
                    merchant.risk_level === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                    {merchant.risk_level}
                  </span>
                </div>
                <div>
                  <p className="text-neutral-600 mb-1">Created</p>
                  <p className="text-neutral-900">{new Date(merchant.created_at).toLocaleDateString()}</p>
                  <p className="text-neutral-600 mb-1">Currency</p>
                  <p className="text-neutral-900">{merchant.currency}</p>
                </div>
              </div>

              <button
                onClick={() => setShowRiskModal(true)}
                className="mt-4 px-4 py-2 text-sm font-medium text-neutral-700 bg-white border border-neutral-300 rounded-lg hover:bg-neutral-50"
              >
                Update Risk Assessment
              </button>
            </div>

            {verifiedInfo && (
              <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6">
                <h2 className="text-xl font-semibold text-neutral-900 mb-4">Business Information</h2>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-neutral-600 mb-1">Business Name</p>
                    <p className="text-neutral-900 font-medium">{verifiedInfo.business_name}</p>
                  </div>
                  <div>
                    <p className="text-neutral-600 mb-1">Industry</p>
                    <p className="text-neutral-900">{verifiedInfo.industry}</p>
                  </div>
                  <div>
                    <p className="text-neutral-600 mb-1">Staff Size</p>
                    <p className="text-neutral-900">{verifiedInfo.staff_size}</p>
                  </div>
                  <div>
                    <p className="text-neutral-600 mb-1">Location</p>
                    <p className="text-neutral-900">{verifiedInfo.location}</p>
                  </div>
                </div>
              </div>
            )}

            {kycDocuments.length > 0 && (
              <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6">
                <h2 className="text-xl font-semibold text-neutral-900 mb-4">KYC Documents</h2>
                <div className="space-y-3">
                  {kycDocuments.map((doc) => (
                    <div key={doc.id} className="flex items-center justify-between p-3 border border-neutral-200 rounded-lg">
                      <div>
                        <p className="text-sm font-medium text-neutral-900">{doc.file_name}</p>
                        <p className="text-xs text-neutral-600">{doc.document_type?.replace('_', ' ')}</p>
                      </div>
                      <a
                        href={doc.file_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm font-medium text-neutral-900 hover:underline"
                      >
                        View
                      </a>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6">
              <h2 className="text-xl font-semibold text-neutral-900 mb-4">KYC Status</h2>

              {kycStatus && (
                <>
                  <div className="mb-4">
                    <span className={`inline-block px-3 py-1 text-sm font-medium rounded-full ${
                      kycStatus.kyc_status === 'verified' ? 'bg-green-100 text-green-700' :
                      kycStatus.kyc_status === 'pending' ? 'bg-yellow-100 text-yellow-700' :
                      kycStatus.kyc_status === 'failed' ? 'bg-red-100 text-red-700' :
                      'bg-neutral-100 text-neutral-700'
                    }`}>
                      {kycStatus.kyc_status}
                    </span>
                  </div>

                  {kycStatus.submitted_at && (
                    <div className="text-sm mb-2">
                      <span className="text-neutral-600">Submitted: </span>
                      <span className="text-neutral-900">{new Date(kycStatus.submitted_at).toLocaleDateString()}</span>
                    </div>
                  )}

                  {kycStatus.rejection_reason && (
                    <div className="p-3 bg-red-50 rounded-lg mb-4">
                      <p className="text-sm text-red-700">{kycStatus.rejection_reason}</p>
                    </div>
                  )}

                  {kycStatus.kyc_status === 'pending' && (
                    <div className="space-y-2 mt-4">
                      <button
                        onClick={handleApproveKYC}
                        disabled={actionLoading}
                        className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center justify-center gap-2 disabled:opacity-50"
                      >
                        <CheckCircle className="w-4 h-4" />
                        {actionLoading ? 'Processing...' : 'Approve KYC'}
                      </button>
                      <button
                        onClick={() => setShowKYCModal(true)}
                        disabled={actionLoading}
                        className="w-full px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center justify-center gap-2 disabled:opacity-50"
                      >
                        <XCircle className="w-4 h-4" />
                        Reject KYC
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6">
              <h2 className="text-xl font-semibold text-neutral-900 mb-4">Balances</h2>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-neutral-600">Available</span>
                  <span className="text-neutral-900 font-medium">{merchant.currency} {parseFloat(merchant.available_balance || 0).toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neutral-600">Pending</span>
                  <span className="text-neutral-900 font-medium">{merchant.currency} {parseFloat(merchant.pending_balance || 0).toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neutral-600">Reserved</span>
                  <span className="text-neutral-900 font-medium">{merchant.currency} {parseFloat(merchant.reserved_balance || 0).toFixed(2)}</span>
                </div>
              </div>
              <button
                onClick={handleSyncBalances}
                disabled={actionLoading}
                className="w-full mt-4 px-4 py-2 text-sm font-medium text-white bg-neutral-900 rounded-lg hover:bg-neutral-800 disabled:opacity-50"
              >
                {actionLoading ? 'Syncing...' : 'Sync Balances'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {showStatusModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-semibold text-neutral-900 mb-4">Update Merchant Status</h3>
            <select
              value={newStatus}
              onChange={(e) => setNewStatus(e.target.value)}
              className="w-full px-4 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-neutral-900 focus:border-transparent mb-4"
            >
              <option value="active">Active</option>
              <option value="suspended">Suspended</option>
              <option value="restricted">Restricted</option>
              <option value="closed">Closed</option>
            </select>
            <div className="flex gap-3">
              <button
                onClick={() => setShowStatusModal(false)}
                className="flex-1 px-4 py-2 text-neutral-700 bg-white border border-neutral-300 rounded-lg hover:bg-neutral-50"
              >
                Cancel
              </button>
              <button
                onClick={handleUpdateStatus}
                disabled={actionLoading}
                className="flex-1 px-4 py-2 bg-neutral-900 text-white rounded-lg hover:bg-neutral-800 disabled:opacity-50"
              >
                {actionLoading ? 'Updating...' : 'Update'}
              </button>
            </div>
          </div>
        </div>
      )}

      {showKYCModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-semibold text-neutral-900 mb-4">KYC Decision</h3>
            <textarea
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              placeholder="Rejection reason (required for rejection)"
              className="w-full px-4 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-neutral-900 focus:border-transparent mb-4"
              rows="4"
            />
            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowKYCModal(false)
                  setRejectionReason('')
                }}
                className="flex-1 px-4 py-2 text-neutral-700 bg-white border border-neutral-300 rounded-lg hover:bg-neutral-50"
              >
                Cancel
              </button>
              <button
                onClick={handleRejectKYC}
                disabled={actionLoading}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                Reject
              </button>
              <button
                onClick={handleApproveKYC}
                disabled={actionLoading}
                className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                Approve
              </button>
            </div>
          </div>
        </div>
      )}

      {showRiskModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-semibold text-neutral-900 mb-4">Update Risk Assessment</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-2">Risk Level</label>
                <select
                  value={riskData.risk_level}
                  onChange={(e) => setRiskData({ ...riskData, risk_level: e.target.value })}
                  className="w-full px-4 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-neutral-900 focus:border-transparent"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-2">Notes</label>
                <textarea
                  value={riskData.notes}
                  onChange={(e) => setRiskData({ ...riskData, notes: e.target.value })}
                  className="w-full px-4 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-neutral-900 focus:border-transparent"
                  rows="3"
                />
              </div>
            </div>
            <div className="flex gap-3 mt-4">
              <button
                onClick={() => setShowRiskModal(false)}
                className="flex-1 px-4 py-2 text-neutral-700 bg-white border border-neutral-300 rounded-lg hover:bg-neutral-50"
              >
                Cancel
              </button>
              <button
                onClick={handleUpdateRisk}
                disabled={actionLoading}
                className="flex-1 px-4 py-2 bg-neutral-900 text-white rounded-lg hover:bg-neutral-800 disabled:opacity-50"
              >
                {actionLoading ? 'Updating...' : 'Update'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
    </>
  )
}

