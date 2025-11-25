const base = import.meta.env.VITE_API_BASE_URL || 'http://51.21.130.249:8000'

function buildUrl(path) {
  return base.replace(/\/$/, '') + path
}

function normalizeErrorPayload(payload, fallback) {
  if (!payload) return fallback

  if (Array.isArray(payload.detail)) {
    const msg = payload.detail.map((d) => d.msg || JSON.stringify(d)).join(', ')
    return msg || fallback
  }
  if (typeof payload.detail === 'string') return payload.detail
  if (typeof payload === 'string') return payload
  return fallback
}

async function request(path, { method = 'GET', token, body } = {}) {
  const isForm = typeof URLSearchParams !== 'undefined' && body instanceof URLSearchParams
  const headers = {}
  if (!isForm) headers['Content-Type'] = 'application/json'
  headers['Accept'] = 'application/json'
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(buildUrl(path), {
    method,
    headers,
    body: body ? (isForm ? body : JSON.stringify(body)) : undefined,
    credentials: 'include',
  })

  if (!res.ok) {
    if (res.status === 401 && path !== '/api/v1/auth/login') {
      localStorage.removeItem('access_token')
      localStorage.removeItem('token')
      localStorage.removeItem('user')

      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }

    let data = null
    try {
      data = await res.json()
    } catch {
      // ignore JSON parse errors for non-JSON error responses
    }

    const message = normalizeErrorPayload(data, res.statusText)
    const err = new Error(message)
    err.status = res.status
    err.payload = data
    throw err
  }
  if (res.status === 204) return null
  return res.json()
}

export const api = {
  register: (data) => request('/api/v1/auth/register', { method: 'POST', body: data }),
  login: (email, password) => request('/api/v1/auth/login', { method: 'POST', body: new URLSearchParams({ username: email, password }) }),
  verifyUser: (token, data) => request('/api/v1/auth/verify', { method: 'POST', token, body: data }),

  createMerchant: (token, data) => request('/api/v1/merchant/account', { method: 'POST', token, body: data }),
  getMerchant: (token) => request('/api/v1/merchant/account', { token }),
  getBalance: (token) => request('/api/v1/merchant/balance', { token }),
  getLimits: (token) => request('/api/v1/merchant/limits', { token }),
  getMerchantBalance: () => request('/api/v1/merchant/balance', { token: localStorage.getItem('access_token') }),
  getMerchantAccount: () => request('/api/v1/merchant/account', { token: localStorage.getItem('access_token') }),
  getCurrentUser: () => request('/api/v1/users/me', { token: localStorage.getItem('access_token') }),


  getCharges: () => request('/v1/charges', { token: localStorage.getItem('access_token') }),
  createCharge: (data) => request('/v1/charges', { method: 'POST', token: localStorage.getItem('access_token'), body: data }),

  createAPIKey: (data) => request('/api/v1/api-keys', { method: 'POST', token: localStorage.getItem('access_token'), body: data }),
  getAPIKeys: () => request('/api/v1/api-keys', { token: localStorage.getItem('access_token') }),
  revokeAPIKey: (keyId, reason) => request(`/api/v1/api-keys/${keyId}`, { method: 'DELETE', token: localStorage.getItem('access_token'), body: { reason: reason || 'Revoked via dashboard' } }),
  updateAPIKey: (keyId, data) => request(`/api/v1/api-keys/${keyId}`, { method: 'PUT', token: localStorage.getItem('access_token'), body: data }),
  rollAPIKey: (keyId) => request(`/api/v1/api-keys/${keyId}/roll`, { method: 'POST', token: localStorage.getItem('access_token') }),

  submitKYCForReview: () => request('/api/v1/kyc/submit', { method: 'POST', token: localStorage.getItem('access_token') }),
  getKYCStatus: () => request('/api/v1/kyc/status', { token: localStorage.getItem('access_token') }),
  getKYCDocuments: () => request('/api/v1/kyc/documents', { token: localStorage.getItem('access_token') }),
  deleteKYCDocument: (documentId) => request(`/api/v1/kyc/documents/${documentId}`, { method: 'DELETE', token: localStorage.getItem('access_token') }),
  submitKYCBusiness: (data) => request('/api/v1/kyc/business', { method: 'POST', token: localStorage.getItem('access_token'), body: data }),
  getKYCBusiness: () => request('/api/v1/kyc/business', { token: localStorage.getItem('access_token') }),
  submitKYCIdentity: (data) => request('/api/v1/kyc/identity', { method: 'POST', token: localStorage.getItem('access_token'), body: data }),
  getKYCIdentity: () => request('/api/v1/kyc/identity', { token: localStorage.getItem('access_token') }),

  getPayoutAccounts: () => request('/api/v1/payout-accounts', { token: localStorage.getItem('access_token') }),
  createPayoutAccount: (data) => request('/api/v1/payout-accounts', { method: 'POST', token: localStorage.getItem('access_token'), body: data }),
  getPayoutAccount: (id) => request(`/api/v1/payout-accounts/${id}`, { token: localStorage.getItem('access_token') }),
  updatePayoutAccount: (id, data) => request(`/api/v1/payout-accounts/${id}`, { method: 'PUT', token: localStorage.getItem('access_token'), body: data }),
  deletePayoutAccount: (accountId) => request(`/api/v1/payout-accounts/${accountId}`, { method: 'DELETE', token: localStorage.getItem('access_token') }),

  getPayouts: () => request('/api/v1/payouts', { token: localStorage.getItem('access_token') }),
  createPayout: (data) => request('/api/v1/payouts', { method: 'POST', token: localStorage.getItem('access_token'), body: data }),
  getPayout: (payoutId) => request(`/api/v1/payouts/${payoutId}`, { token: localStorage.getItem('access_token') }),
  cancelPayout: (payoutId) => request(`/api/v1/payouts/${payoutId}/cancel`, { method: 'PUT', token: localStorage.getItem('access_token') }),
  processPayoutManual: (payoutId) => request(`/api/v1/payouts/${payoutId}/process`, { method: 'POST', token: localStorage.getItem('access_token') }),

  adminListPayouts: (params = {}) => {
    const qs = new URLSearchParams(params).toString()
    return request(`/api/v1/admin/payouts${qs ? `?${qs}` : ''}`, { token: localStorage.getItem('access_token') })
  },
  adminGetMerchants: (skip = 0, limit = 100, search = null) => {
    let url = `/api/v1/admin/merchants?skip=${skip}&limit=${limit}`
    if (search) url += `&search=${encodeURIComponent(search)}`
    return request(url, { token: localStorage.getItem('access_token') })
  },
  adminGetMerchantDetails: (merchantId) => request(`/api/v1/admin/merchants/${merchantId}`, { token: localStorage.getItem('access_token') }),
  adminUpdateMerchantStatus: (merchantId, status) => request(`/api/v1/admin/merchants/${merchantId}/status`, { method: 'PUT', token: localStorage.getItem('access_token'), body: { status } }),
  adminUpdateRiskAssessment: (merchantId, riskData) => request(`/api/v1/admin/merchants/${merchantId}/risk`, { method: 'PUT', token: localStorage.getItem('access_token'), body: riskData }),
  adminApproveKYC: (userId) => request(`/api/v1/admin/kyc/${userId}/approve`, { method: 'POST', token: localStorage.getItem('access_token') }),
  adminRejectKYC: (userId, rejectionReason) => request(`/api/v1/admin/kyc/${userId}/reject`, { method: 'POST', token: localStorage.getItem('access_token'), body: { rejection_reason: rejectionReason } }),
  adminGetTransactions: (skip = 0, limit = 100, merchantId = null) => {
    let url = `/api/v1/admin/transactions?skip=${skip}&limit=${limit}`
    if (merchantId) url += `&merchant_id=${merchantId}`
    return request(url, { token: localStorage.getItem('access_token') })
  },
  adminGetAuditLogs: (skip = 0, limit = 100, userId = null, action = null) => {
    let url = `/api/v1/admin/audit-logs?skip=${skip}&limit=${limit}`
    if (userId) url += `&user_id=${userId}`
    if (action) url += `&action=${encodeURIComponent(action)}`
    return request(url, { token: localStorage.getItem('access_token') })
  },
  adminPromoteUser: (userId) => request(`/api/v1/admin/users/${userId}/promote`, { method: 'POST', token: localStorage.getItem('access_token') }),
  adminSyncBalances: (merchantId) => request(`/api/v1/admin/merchants/${merchantId}/sync-balances`, { method: 'POST', token: localStorage.getItem('access_token') }),

  getNotifications: (skip = 0, limit = 50) => request(`/api/v1/notifications?skip=${skip}&limit=${limit}`, { token: localStorage.getItem('access_token') }),
  getUnreadNotificationsCount: () => request('/api/v1/notifications/unread_count', { token: localStorage.getItem('access_token') }),
  markNotificationRead: (id) => request(`/api/v1/notifications/${id}/read`, { method: 'PUT', token: localStorage.getItem('access_token') }),
  markAllNotificationsRead: () => request('/api/v1/notifications/read_all', { method: 'PUT', token: localStorage.getItem('access_token') }),

  changePassword: (data) => request('/api/v1/account/change-password', { method: 'PUT', token: localStorage.getItem('access_token'), body: data }),
  deleteAccount: () => request('/api/v1/users/me', { method: 'DELETE', token: localStorage.getItem('access_token') }),
  refreshUserData: () => request('/api/v1/users/me/refresh', { token: localStorage.getItem('access_token') }),
  getSettlementSchedule: () => request('/api/v1/settlements/schedule', { token: localStorage.getItem('access_token') }),
  updateSettlementSchedule: (data) => request('/api/v1/settlements/schedule', { method: 'PUT', token: localStorage.getItem('access_token'), body: data }),
}