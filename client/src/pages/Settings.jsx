/* eslint-disable no-unused-vars */
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import { api } from '../lib/apiClient'

export default function Settings() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [user, setUser] = useState(null)
  const [success, setSuccess] = useState('')
  const [error, setError] = useState('')
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [deleteLoading, setDeleteLoading] = useState(false)
  const [deleteError, setDeleteError] = useState('')

  const [showPasswordModal, setShowPasswordModal] = useState(false)
  const [passwordData, setPasswordData] = useState({
    oldPassword: '',
    newPassword: '',
    confirmPassword: ''
  })
  const [passwordError, setPasswordError] = useState('')
  const [passwordLoading, setPasswordLoading] = useState(false)
  const [passwordSuccess, setPasswordSuccess] = useState(false)

  const [payoutAccounts, setPayoutAccounts] = useState([])
  const [newAccount, setNewAccount] = useState({ bank_name: '', account_holder_name: '', account_number: '', routing_number: '', bank_country: '', currency: 'USD' })
  const [accountsLoading, setAccountsLoading] = useState(false)
  const [schedule, setSchedule] = useState(null)
  const [scheduleLoading, setScheduleLoading] = useState(false)
  const [scheduleSaving, setScheduleSaving] = useState(false)

  const loadSettings = async () => {
    try {
      setLoading(true)
      const current = await api.getCurrentUser()
      if (current) {
        setUser((prev) => ({ ...prev, ...current }))
      }
    } catch (error) {
      setError(error?.message || 'Failed to load settings')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      navigate('/login')
      return
    }

    const userData = localStorage.getItem('user')
    if (userData && userData !== 'undefined') {
      try {
        setUser(JSON.parse(userData))
      } catch (err) {
        console.warn('Failed to parse cached user record', err)
      }
    }

    loadSettings()
  }, [navigate])

  const handleLogout = () => {
    localStorage.clear()
    navigate('/login')
  }

  const handleDeleteAccount = async () => {
    setDeleteError('')
    setDeleteLoading(true)

    try {
      await api.deleteAccount()
      localStorage.clear()
      window.location.href = '/login'
    } catch (err) {
      setDeleteError(err.message || 'Failed to delete account')
    } finally {
      setDeleteLoading(false)
    }
  }

  const handlePasswordChange = async () => {
    setPasswordError('')
    setPasswordSuccess(false)

    if (!passwordData.oldPassword || !passwordData.newPassword || !passwordData.confirmPassword) {
      setPasswordError('All fields are required')
      return
    }

    if (passwordData.newPassword.length < 8) {
      setPasswordError('New password must be at least 8 characters')
      return
    }

    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setPasswordError('New passwords do not match')
      return
    }

    if (passwordData.oldPassword === passwordData.newPassword) {
      setPasswordError('New password must be different from old password')
      return
    }

    setPasswordLoading(true)

    try {
      await api.changePassword({
        old_password: passwordData.oldPassword,
        new_password: passwordData.newPassword,
        confirm_password: passwordData.confirmPassword
      })

      setPasswordSuccess(true)
      setPasswordData({ oldPassword: '', newPassword: '', confirmPassword: '' })

      setTimeout(() => {
        setShowPasswordModal(false)
        setPasswordSuccess(false)
      }, 2000)
    } catch (err) {
      setPasswordError(err.message || 'Failed to change password')
    } finally {
      setPasswordLoading(false)
    }
  }

  const loadPayoutAccounts = async () => {
    try {
      setAccountsLoading(true)
      const acc = await api.getPayoutAccounts()
      setPayoutAccounts(acc || [])
    } catch (err) {
      console.warn('Failed to load payout accounts', err)
    } finally {
      setAccountsLoading(false)
    }
  }

  const loadSchedule = async () => {
    try {
      setScheduleLoading(true)
      const s = await api.getSettlementSchedule()
      if (s) {
        const allowed = ['daily', 'weekly', 'bi_weekly', 'monthly']
        let sched = s.schedule
        if (typeof sched === 'string') sched = sched.toLowerCase()
        if (!allowed.includes(sched)) {
          const map = {
            'daily': 'daily', 'weekly': 'weekly', 'bi_weekly': 'bi_weekly', 'bi-weekly': 'bi_weekly', 'monthly': 'monthly', 'manual': 'daily', 'daily_old': 'daily'
          }
          sched = map[schedule?.schedule?.toLowerCase?.() || s.schedule?.toLowerCase?.()] || (typeof s.schedule === 'string' ? s.schedule.toLowerCase() : 'daily')
          if (!allowed.includes(sched)) sched = 'daily'
        }
        const normalized = {
          ...s,
          schedule: sched,
          delay_days: s.delay_days !== undefined && s.delay_days !== null ? Number(s.delay_days) : 0,
          minimum_payout_amount: s.minimum_payout_amount !== undefined && s.minimum_payout_amount !== null ? Number(s.minimum_payout_amount) : null
        }
        setSchedule(normalized)
      } else {
        setSchedule({ schedule: 'daily', delay_days: 0, minimum_payout_amount: null })
      }
    } catch (err) {
      console.warn('Failed to load settlement schedule', err)
    } finally {
      setScheduleLoading(false)
    }
  }

  useEffect(() => {
    loadPayoutAccounts()
    loadSchedule()
  }, [])

  useEffect(() => { if (typeof setSuccess === 'function') { /* no-op */ } }, [setSuccess])

  const createAccount = async () => {
    try {
      await api.createPayoutAccount(newAccount)
      setNewAccount({ bank_name: '', account_holder_name: '', account_number: '', routing_number: '', bank_country: '', currency: 'USD' })
      await loadPayoutAccounts()
      setSuccess('Payout account added')
      setTimeout(() => setSuccess(''), 3000)
    } catch (err) {
      alert(err.message || 'Failed to create account')
    }
  }

  const deleteAccount = async (id) => {
    if (!window.confirm('Delete this payout account?')) return
    try {
      await api.deletePayoutAccount(id)
      await loadPayoutAccounts()
      setSuccess('Payout account deleted')
      setTimeout(() => setSuccess(''), 3000)
    } catch (err) {
      alert(err.message || 'Failed to delete account')
    }
  }

  const updatePayoutAccount = async (id, data) => {
    try {
      await api.updatePayoutAccount(id, data)
      await loadPayoutAccounts()
      setSuccess('Payout account updated')
      setTimeout(() => setSuccess(''), 3000)
    } catch (err) {
      alert(err.message || 'Failed to update account')
    }
  }

  const saveSchedule = async () => {
    try {
      setScheduleSaving(true)
      const payload = {
        schedule: schedule.schedule,
        delay_days: Number(schedule.delay_days || 0),
        minimum_payout_amount: schedule.minimum_payout_amount === null || schedule.minimum_payout_amount === undefined ? null : Number(schedule.minimum_payout_amount)
      }
      await api.updateSettlementSchedule(payload)
      await loadSchedule()
      setSuccess('Settlement schedule updated')
      setTimeout(() => setSuccess(''), 3000)
    } catch (err) {
      alert(err.message || 'Failed to update schedule')
    } finally {
      setScheduleSaving(false)
    }
  }

  // end payout account & schedule helpers

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="min-h-screen bg-neutral-50 flex items-center justify-center">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-neutral-900 mb-4"></div>
            <p className="text-neutral-600">Loading settings...</p>
          </div>
        </div>
      </>
    )
  }

  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-neutral-50">
        <div className="max-w-4xl mx-auto px-4 md:px-6 py-6 md:py-8">
          
          <div className="mb-6 md:mb-8">
            <h1 className="text-2xl md:text-3xl font-bold text-neutral-900 mb-2">Settings</h1>
            <p className="text-sm md:text-base text-neutral-600">Manage your account and preferences</p>
          </div>

          
          {success && (
            <div className="mb-6 p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 flex items-center gap-3">
              <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <p className="text-sm font-medium">{success}</p>
            </div>
          )}

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-800 flex items-center gap-3">
              <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <p className="text-sm font-medium">{error}</p>
            </div>
          )}

          <div className="space-y-6">
            
            <div className="bg-white rounded-xl border border-neutral-200 shadow-sm">
              <div className="px-6 py-4 border-b border-neutral-200">
                <h2 className="text-lg font-bold text-neutral-900">Account Information</h2>
                <p className="text-sm text-neutral-600 mt-1">Your personal account details</p>
              </div>
              <div className="p-6 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold text-neutral-700 mb-2">Full Name</label>
                    <input
                      type="text"
                      value={user?.name || ''}
                      className="w-full px-4 py-3 border border-neutral-300 rounded-lg bg-neutral-50 text-neutral-900 font-medium"
                      disabled
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-neutral-700 mb-2">Email Address</label>
                    <input
                      type="email"
                      value={user?.email || ''}
                      className="w-full px-4 py-3 border border-neutral-300 rounded-lg bg-neutral-50 text-neutral-900 font-medium"
                      disabled
                    />
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold text-neutral-700 mb-2">Country</label>
                    <input
                      type="text"
                      value={user?.country || 'Not set'}
                      className="w-full px-4 py-3 border border-neutral-300 rounded-lg bg-neutral-50 text-neutral-900 font-medium"
                      disabled
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-neutral-700 mb-2">Phone Number</label>
                    <input
                      type="text"
                      value={user?.phone_number || 'Not set'}
                      className="w-full px-4 py-3 border border-neutral-300 rounded-lg bg-neutral-50 text-neutral-900 font-medium"
                      disabled
                    />
                  </div>
                </div>
                <p className="text-xs text-neutral-500 mt-4">
                  <svg className="w-4 h-4 inline mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                  Contact support to update your account information
                </p>
              </div>
            </div>

            
            <div className="bg-white rounded-xl border border-neutral-200 shadow-sm">
              <div className="px-6 py-4 border-b border-neutral-200">
                <h2 className="text-lg font-bold text-neutral-900">Security</h2>
                <p className="text-sm text-neutral-600 mt-1">Manage your password and security settings</p>
              </div>
              <div className="p-6 space-y-4">
                <button
                  onClick={() => setShowPasswordModal(true)}
                  className="w-full md:w-auto px-6 py-3 bg-neutral-900 hover:bg-neutral-800 text-white rounded-lg font-semibold transition-colors flex items-center justify-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                  </svg>
                  Change Password
                </button>
              </div>
            </div>

            
            <div className="bg-white rounded-xl border border-neutral-200 shadow-sm">
              <div className="px-6 py-4 border-b border-neutral-200">
                <h2 className="text-lg font-bold text-neutral-900">Notifications</h2>
                <p className="text-sm text-neutral-600 mt-1">Configure how you receive updates</p>
              </div>
              <div className="p-6 space-y-4">
                <label className="flex items-center justify-between p-4 bg-neutral-50 rounded-lg cursor-pointer hover:bg-neutral-100 transition-colors">
                  <div>
                    <div className="font-semibold text-neutral-900">Email Notifications</div>
                    <div className="text-sm text-neutral-600 mt-1">Receive updates about charges and transfers</div>
                  </div>
                  <input type="checkbox" defaultChecked className="w-5 h-5 rounded border-neutral-300 text-neutral-900 focus:ring-neutral-900" />
                </label>
                <label className="flex items-center justify-between p-4 bg-neutral-50 rounded-lg cursor-pointer hover:bg-neutral-100 transition-colors">
                  <div>
                    <div className="font-semibold text-neutral-900">Security Alerts</div>
                    <div className="text-sm text-neutral-600 mt-1">Get notified about account security events</div>
                  </div>
                  <input type="checkbox" defaultChecked className="w-5 h-5 rounded border-neutral-300 text-neutral-900 focus:ring-neutral-900" />
                </label>
              </div>
            </div>

            <div className="bg-white rounded-xl border border-neutral-200 shadow-sm">
              <div className="px-6 py-4 border-b border-neutral-200">
                <h2 className="text-lg font-bold text-neutral-900">Payout Accounts</h2>
                <p className="text-sm text-neutral-600 mt-1">Manage your bank accounts for withdrawals</p>
              </div>
              <div className="p-6 space-y-4">
                <div>
                  <h3 className="text-sm font-semibold text-neutral-700 mb-2">Add Bank Account</h3>
                  <div className="grid md:grid-cols-2 gap-3">
                    <input value={newAccount.bank_name} onChange={(e)=>setNewAccount({...newAccount, bank_name:e.target.value})} placeholder="Bank Name" className="px-3 py-2 border rounded" />
                    <input value={newAccount.account_holder_name} onChange={(e)=>setNewAccount({...newAccount, account_holder_name:e.target.value})} placeholder="Account holder name" className="px-3 py-2 border rounded" />
                    <input value={newAccount.account_number} onChange={(e)=>setNewAccount({...newAccount, account_number:e.target.value})} placeholder="Account number" className="px-3 py-2 border rounded" />
                    <input value={newAccount.routing_number} onChange={(e)=>setNewAccount({...newAccount, routing_number:e.target.value})} placeholder="Routing number" className="px-3 py-2 border rounded" />
                    <select value={newAccount.currency} onChange={(e)=>setNewAccount({...newAccount, currency:e.target.value})} className="px-3 py-2 border rounded">
                      <option>USD</option>
                      <option>NGN</option>
                      <option>EUR</option>
                    </select>
                    <div className="flex items-center gap-2">
                      <label className="text-sm">Set Primary</label>
                      <input type="checkbox" checked={newAccount.is_primary||false} onChange={(e)=>setNewAccount({...newAccount, is_primary: e.target.checked})} />
                    </div>
                  </div>
                  <div className="mt-3 flex gap-2">
                    <button onClick={createAccount} className="px-4 py-2 bg-neutral-900 text-white rounded">Add Account</button>
                    <button onClick={()=>setNewAccount({ bank_name: '', account_holder_name: '', account_number: '', routing_number: '', bank_country: '', currency: 'USD' })} className="px-4 py-2 border rounded">Reset</button>
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-neutral-700 mb-2">Linked Accounts</h3>
                  {accountsLoading ? <div>Loading accounts...</div> : (
                    <div className="space-y-2">
                      {payoutAccounts.length === 0 && <div className="text-sm text-neutral-600">No accounts added yet.</div>}
                      {payoutAccounts.map(ac => (
                        <div key={ac.id} className="flex items-center justify-between p-3 border rounded">
                          <div>
                            <div className="font-medium">{ac.bank_name} • {ac.account_number_last4}</div>
                            <div className="text-xs text-neutral-600">{ac.account_holder_name} • {ac.currency} {ac.is_primary ? '• Primary' : ''}</div>
                          </div>
                          <div className="flex gap-2">
                            {!ac.is_primary && <button onClick={()=>{ updatePayoutAccount(ac.id, { is_primary: true }) }} className="text-sm px-3 py-1 border rounded">Set Primary</button>}
                            <button onClick={()=>deleteAccount(ac.id)} className="text-sm px-3 py-1 border rounded text-red-600">Delete</button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl border border-neutral-200 shadow-sm">
              <div className="px-6 py-4 border-b border-neutral-200">
                <h2 className="text-lg font-bold text-neutral-900">Settlement Schedule</h2>
                <p className="text-sm text-neutral-600 mt-1">When your funds are settled and available for payout</p>
              </div>
              <div className="p-6 space-y-4">
                {scheduleLoading ? (
                  <div>Loading schedule...</div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3 items-end">
                    <div>
                      <label className="block text-sm text-neutral-700 mb-1">Frequency</label>
                      <select value={schedule?.schedule || 'daily'} onChange={(e)=>setSchedule({...schedule, schedule: e.target.value})} className="w-full px-3 py-2 border rounded">
                        <option value="daily">Daily</option>
                        <option value="weekly">Weekly</option>
                        <option value="bi_weekly">Bi-weekly</option>
                        <option value="monthly">Monthly</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm text-neutral-700 mb-1">Delay days</label>
                      <input type="number" value={schedule?.delay_days ?? 0} onChange={(e)=>setSchedule({...schedule, delay_days: Number(e.target.value)})} className="w-full px-3 py-2 border rounded" />
                    </div>

                    <div>
                      <label className="block text-sm text-neutral-700 mb-1">Minimum payout</label>
                      <input type="number" step="0.01" value={schedule?.minimum_payout_amount ?? 0} onChange={(e)=>setSchedule({...schedule, minimum_payout_amount: Number(e.target.value)})} className="w-full px-3 py-2 border rounded" />
                    </div>

                    <div className="md:col-span-3">
                      <div className="mt-3 flex gap-2">
                        <button onClick={saveSchedule} disabled={scheduleSaving} className="px-4 py-2 bg-neutral-900 text-white rounded">{scheduleSaving ? 'Saving...' : 'Save schedule'}</button>
                        <button onClick={loadSchedule} className="px-4 py-2 border rounded">Reload</button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
        
        <div className="max-w-4xl mx-auto px-4 md:px-6 py-6 md:py-8">
          <div className="bg-white rounded-xl border border-red-200 shadow-sm">
            <div className="px-6 py-4 border-b border-red-200">
                <h2 className="text-lg font-bold text-red-600">Danger Zone</h2>
                <p className="text-sm text-neutral-600 mt-1">Irreversible and destructive actions</p>
              </div>
              <div className="p-6 space-y-4">
                <div className="flex flex-col md:flex-row gap-3">
                  <button
                    onClick={handleLogout}
                    className="flex-1 px-6 py-3 bg-neutral-600 hover:bg-neutral-700 text-white rounded-lg font-semibold transition-colors flex items-center justify-center gap-2"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                    </svg>
                    Log Out
                  </button>
                  <button
                    onClick={() => setShowDeleteModal(true)}
                    className="flex-1 px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg font-semibold transition-colors flex items-center justify-center gap-2"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                    Delete Account
                  </button>
                </div>
              </div>
          </div>
        </div>
      </div>

      
      {showPasswordModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50 backdrop-blur-sm" onClick={() => setShowPasswordModal(false)}>
          <div className="bg-white rounded-2xl max-w-md w-full shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="px-6 py-5 border-b border-neutral-200">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xl font-bold text-neutral-900">Change Password</h3>
                  <p className="text-sm text-neutral-600 mt-1">Update your account password</p>
                </div>
                <button
                  onClick={() => {
                    setShowPasswordModal(false)
                    setPasswordError('')
                    setPasswordSuccess(false)
                    setPasswordData({ oldPassword: '', newPassword: '', confirmPassword: '' })
                  }}
                  className="w-8 h-8 flex items-center justify-center rounded-lg text-neutral-400 hover:text-neutral-600 hover:bg-neutral-100 transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            <div className="px-6 py-6">
              {passwordSuccess && (
                <div className="mb-6 p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center gap-3">
                  <svg className="w-5 h-5 text-emerald-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <p className="text-sm text-emerald-800 font-medium">Password changed successfully!</p>
                </div>
              )}

              {passwordError && (
                <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
                  <svg className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                  <p className="text-sm text-red-800">{passwordError}</p>
                </div>
              )}

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold text-neutral-700 mb-2">
                    Current Password
                  </label>
                  <input
                    type="password"
                    value={passwordData.oldPassword}
                    onChange={(e) => setPasswordData({ ...passwordData, oldPassword: e.target.value })}
                    className="w-full px-4 py-3 border border-neutral-300 rounded-xl focus:ring-2 focus:ring-neutral-900 focus:border-neutral-900 transition-all"
                    placeholder="Enter your current password"
                    disabled={passwordLoading}
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-neutral-700 mb-2">
                    New Password
                  </label>
                  <input
                    type="password"
                    value={passwordData.newPassword}
                    onChange={(e) => setPasswordData({ ...passwordData, newPassword: e.target.value })}
                    className="w-full px-4 py-3 border border-neutral-300 rounded-xl focus:ring-2 focus:ring-neutral-900 focus:border-neutral-900 transition-all"
                    placeholder="Enter new password (min. 8 characters)"
                    disabled={passwordLoading}
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-neutral-700 mb-2">
                    Confirm New Password
                  </label>
                  <input
                    type="password"
                    value={passwordData.confirmPassword}
                    onChange={(e) => setPasswordData({ ...passwordData, confirmPassword: e.target.value })}
                    className="w-full px-4 py-3 border border-neutral-300 rounded-xl focus:ring-2 focus:ring-neutral-900 focus:border-neutral-900 transition-all"
                    placeholder="Confirm your new password"
                    disabled={passwordLoading}
                  />
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  type="button"
                  onClick={() => {
                    setShowPasswordModal(false)
                    setPasswordError('')
                    setPasswordSuccess(false)
                    setPasswordData({ oldPassword: '', newPassword: '', confirmPassword: '' })
                  }}
                  className="flex-1 px-6 py-3 bg-white border-2 border-neutral-300 hover:border-neutral-400 hover:bg-neutral-50 text-neutral-700 rounded-xl font-semibold transition-all"
                  disabled={passwordLoading}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handlePasswordChange}
                  className="flex-1 px-6 py-3 bg-neutral-900 hover:bg-neutral-800 text-white rounded-xl font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  disabled={passwordLoading}
                >
                  {passwordLoading ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      <span>Updating...</span>
                    </>
                  ) : (
                    'Change Password'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50 backdrop-blur-sm" onClick={() => setShowDeleteModal(false)}>
          <div className="bg-white rounded-2xl max-w-md w-full shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="px-6 py-5 border-b border-neutral-200">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xl font-bold text-red-600">Delete Account</h3>
                  <p className="text-sm text-neutral-600 mt-1">This action cannot be undone</p>
                </div>
                <button
                  onClick={() => setShowDeleteModal(false)}
                  className="w-8 h-8 flex items-center justify-center rounded-lg text-neutral-400 hover:text-neutral-600 hover:bg-neutral-100 transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            {deleteError && (
              <div className="mx-6 mt-4 p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
                <svg className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <p className="text-sm text-red-800">{deleteError}</p>
              </div>
            )}

            <div className="px-6 py-6">
              <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6">
                <div className="flex gap-3">
                  <svg className="w-6 h-6 text-red-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <div>
                    <h4 className="text-sm font-bold text-red-900 mb-2">Warning: This will permanently delete:</h4>
                    <ul className="text-sm text-red-800 space-y-1 list-disc list-inside">
                      <li>Your account and profile</li>
                      <li>All merchant data and settings</li>
                      <li>Transaction history</li>
                      <li>API keys and integrations</li>
                      <li>All associated data</li>
                    </ul>
                  </div>
                </div>
              </div>

              <p className="text-sm text-neutral-700 mb-6">
                Are you absolutely sure you want to delete your account? Type <strong className="font-bold text-neutral-900">DELETE</strong> below to confirm.
              </p>

              <input
                type="text"
                placeholder="Type DELETE to confirm"
                className="w-full px-4 py-3 border border-neutral-300 rounded-xl focus:ring-2 focus:ring-red-600 focus:border-red-600 transition-all mb-6"
                id="delete-confirmation"
              />

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowDeleteModal(false)}
                  className="flex-1 px-6 py-3 bg-white border-2 border-neutral-300 hover:border-neutral-400 hover:bg-neutral-50 text-neutral-700 rounded-xl font-semibold transition-all"
                  disabled={deleteLoading}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const input = document.getElementById('delete-confirmation')
                    if (input.value === 'DELETE') {
                      handleDeleteAccount()
                    } else {
                      setDeleteError('Please type DELETE to confirm')
                    }
                  }}
                  className="flex-1 px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-xl font-semibold transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                  disabled={deleteLoading}
                >
                  {deleteLoading ? (
                    <>
                      <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Deleting...
                    </>
                  ) : 'Delete My Account'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
