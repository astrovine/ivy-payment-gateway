import { useState, useEffect, useCallback } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import Navbar from '../components/Navbar'
import { api } from '../lib/apiClient'
import { useAuth } from '../context/AuthContext'

const getTimeBasedGreeting = () => {
  const hour = new Date().getHours()
  const greetings = {
    morning: ["Good morning", "Rise and shine", "Top of the morning", "The sun is shinning and so are you","What a beautiful morning", "What are we upto today"],
    afternoon: ["Good afternoon", "What a wonderful afternoon", "Hope you're having a great day", "Welcome back", "Afternoon"],
    evening: ["Good evening", "Hope you had a productive day", "Great to see you", "Evening"],
    night: ["Good evening", "Burning the midnight oil", "Working late", "Still here","Saving the city"]
  }

  let greetingArray
  if (hour >= 5 && hour < 12) {
    greetingArray = greetings.morning
  } else if (hour >= 12 && hour < 17) {
    greetingArray = greetings.afternoon
  } else if (hour >= 17 && hour < 21) {
    greetingArray = greetings.evening
  } else {
    greetingArray = greetings.night
  }

  const randomIndex = Math.floor(Math.random() * greetingArray.length)
  return greetingArray[randomIndex]
}

const currencySymbols = {
  USD: '$',
  NGN: '₦',
  EUR: '€',
  GBP: '£'
}

export default function Dashboard() {
  const navigate = useNavigate()
  const { logout } = useAuth()
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [user, setUser] = useState(null)
  const [balance, setBalance] = useState(null)
  const [charges, setCharges] = useState([])
  const [payouts, setPayouts] = useState([])
  const [payoutAccounts, setPayoutAccounts] = useState([])
  const [apiKeys, setApiKeys] = useState([])
  const [showCreateCharge, setShowCreateCharge] = useState(false)
  const [chargeForm, setChargeForm] = useState({
    amount: '',
    currency: 'NGN',
    description: ''
  })
  const [chargeError, setChargeError] = useState('')
  const [creatingCharge, setCreatingCharge] = useState(false)
  const [greeting, setGreeting] = useState('')
  const [overlayActive, setOverlayActive] = useState(false)

  const loadDashboard = useCallback(async () => {
    try {
      setLoading(true)

      const balanceData = await api.getMerchantBalance().catch(() => {
        return { available_balance: '0', pending_balance: '0', currency: 'USD' }
      })
      setBalance(balanceData)

      const chargesData = await api.getCharges().catch(() => {
        return []
      })
      const chargesArray = Array.isArray(chargesData) ? chargesData : chargesData?.charges || []
      setCharges(chargesArray)

      const payoutsData = await api.getPayouts().catch(() => {
        return []
      })
      const payoutsArray = Array.isArray(payoutsData) ? payoutsData : payoutsData?.payouts || []
      setPayouts(payoutsArray)

      const accountsData = await api.getPayoutAccounts().catch(() => [])
      setPayoutAccounts(Array.isArray(accountsData) ? accountsData : accountsData?.accounts || [])

      const keysData = await api.getAPIKeys().catch(() => {
        return []
      })
      const keysArray = Array.isArray(keysData) ? keysData : keysData?.api_keys || []
      setApiKeys(keysArray)
    } catch (err) {
      console.error('Error loading dashboard data:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  const refreshData = useCallback(async () => {
    setRefreshing(true)
    await loadDashboard()
    setRefreshing(false)
  }, [loadDashboard])

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      navigate('/login')
      return
    }

    const userData = localStorage.getItem('user')
    if (userData && userData !== 'undefined' && userData !== 'null') {
      try {
        const parsedUser = JSON.parse(userData)
        setUser(parsedUser)
      } catch {
        localStorage.removeItem('user')
      }
    }

    const ensureUserAndData = async () => {
      try {
        const me = await api.getCurrentUser().catch(() => null)
        if (me) {
          const normalized = {
            name: me?.name,
            email: me?.email,
            country: me?.country,
            id: me?.id,
            is_superadmin: me?.is_superadmin || false,
            merchant_info: me?.merchant_info || null,
            verification_status: me?.merchant_info?.verification_status || me?.verification_status || null,
            onboarding_stage: me?.onboarding_stage || null
          }
          setUser(normalized)
          localStorage.setItem('user', JSON.stringify(normalized))

          const hasMerchantAccount = normalized?.merchant_info || normalized?.onboarding_stage === 'active'
          const isVerified = normalized?.merchant_info?.verification_status === 'verified' || normalized?.onboarding_stage === 'active' || normalized?.verification_status === 'verified'
          const snoozeRaw = localStorage.getItem('onboarding_snooze_until')
          if (snoozeRaw) {
            const until = Number(snoozeRaw)
            if (!Number.isNaN(until) && Date.now() < until) {
              setOverlayActive(false)
            } else {
              setOverlayActive(hasMerchantAccount && !isVerified)
            }
          } else {
            setOverlayActive(hasMerchantAccount && !isVerified)
          }
        }
      } catch {
        // ignore
      }

      setGreeting(getTimeBasedGreeting())
      await loadDashboard()

      const interval = setInterval(() => {
        refreshData()
      }, 60000)

      return () => clearInterval(interval)
    }

    ensureUserAndData()


  }, [navigate, loadDashboard, refreshData])

  useEffect(() => {
    const updateOverlay = () => {
      try {
        if (user?.is_superadmin) {
          setOverlayActive(false)
          return
        }

        const hasMerchantAccount = user?.merchant_info || user?.onboarding_stage === 'active'
        const isVerified = user?.merchant_info?.verification_status === 'verified' ||
                          user?.onboarding_stage === 'active' ||
                          user?.verification_status === 'verified'

        const snoozeRaw = localStorage.getItem('onboarding_snooze_until')
        if (snoozeRaw) {
          const until = Number(snoozeRaw)
          if (Number.isNaN(until) || Date.now() >= until) {
            localStorage.removeItem('onboarding_snooze_until')
          } else {
            setOverlayActive(false)
            return
          }
        }

        setOverlayActive(hasMerchantAccount && !isVerified)
      } catch {
        setOverlayActive(false)
      }
    }
    updateOverlay()
  }, [user])

  const handleCreateCharge = async (e) => {
    e.preventDefault()
    setChargeError('')

    if (!chargeForm.amount || parseFloat(chargeForm.amount) <= 0) {
      setChargeError('Please enter a valid amount')
      return
    }

    if (!chargeForm.description) {
      setChargeError('Please enter a description')
      return
    }

    try {
      setCreatingCharge(true)

      const chargeData = {
        amount: Number(chargeForm.amount).toFixed(2),
        currency: chargeForm.currency,
        description: chargeForm.description,
        idempotency_key: `charge-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        payment_token: 'tok_valid_success'
      }

      await api.createCharge(chargeData)

      setChargeForm({ amount: '', currency: 'NGN', description: '' })
      setShowCreateCharge(false)

      await new Promise(resolve => setTimeout(resolve, 2000))

      await loadDashboard()

    } catch (err) {
      setChargeError(err.message || 'Failed to create charge. Please try again.')
    } finally {
      setCreatingCharge(false)
    }
  }

  const formatCurrency = (amount, currency = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency
    }).format(parseFloat(amount) || 0)
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    const now = new Date()
    const diff = Math.floor((now - date) / 1000)

    if (diff < 60) return `${diff}s ago`
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  }

  const getStatusStyles = (status) => {
    const styles = {
      succeeded: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      pending: 'bg-amber-50 text-amber-700 border-amber-200',
      failed: 'bg-red-50 text-red-700 border-red-200',
      refunded: 'bg-neutral-100 text-neutral-700 border-neutral-200'
    }
    return styles[status] || styles.pending
  }

  const renderTransactionTitle = (tx) => {
    if (tx && tx.payout_account_id) {
      const acct = payoutAccounts.find(a => a.id === tx.payout_account_id)
      const acctLabel = acct ? `${acct.bank_name} • ${acct.account_number_last4 || acct.account_number?.slice(-4) || '****'}` : `Account ${tx.payout_account_id}`
      return `Payout to ${acctLabel}`
    }

    return tx?.description || (tx?.object === 'charge' ? 'Charge' : 'Transaction')
  }

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="min-h-screen bg-neutral-50 flex items-center justify-center">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-neutral-900 mb-4"></div>
            <p className="text-neutral-600">Loading your dashboard...</p>
          </div>
        </div>
      </>
    )
  }

  const userName = user?.name || user?.email?.split('@')[0] || 'there'
  const availableBalance = parseFloat(balance?.available_balance || 0)
  const pendingBalance = parseFloat(balance?.pending_balance || 0)
  const totalVolume = availableBalance + pendingBalance

  const goToVerify = () => navigate('/onboarding/verify')
  const handleOverlayLogout = () => {
    try {
      if (logout) logout()
    } catch {
      // ignore
    }
    localStorage.removeItem('user')
    localStorage.removeItem('onboarding_snooze_until')
    navigate('/')
  }

  return (
    <>
      <Navbar />
      <div className={`min-h-screen bg-neutral-50 ${overlayActive ? 'relative' : ''}`}>
        <div className={`w-full px-3 sm:px-4 md:px-6 lg:max-w-7xl lg:mx-auto py-4 md:py-6 lg:py-8 ${overlayActive ? 'blur-sm pointer-events-none select-none' : ''}`}>

          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6 md:mb-10">
            <div>
              <h1 className="text-2xl md:text-3xl lg:text-4xl font-semibold text-neutral-900 mb-1.5 tracking-tight">
                {greeting}, {userName}!
              </h1>
              <p className="text-sm md:text-base text-neutral-600 tracking-[-0.01em]">Here's what's happening with your business today</p>
            </div>
            <div className="flex gap-2 md:gap-3">
              <button
                onClick={refreshData}
                disabled={refreshing}
                className="px-3 md:px-4 py-2 bg-neutral-100 hover:bg-neutral-200 text-neutral-700 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                <svg className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span className="hidden sm:inline">{refreshing ? 'Refreshing...' : 'Refresh'}</span>
              </button>
              <button
                onClick={() => setShowCreateCharge(true)}
                className="btn-primary px-4 md:px-6 py-2 flex items-center gap-2 text-sm md:text-base"
              >
                <svg className="w-4 h-4 md:w-5 md:h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                </svg>
                <span className="hidden sm:inline">Create Charge</span>
                <span className="sm:hidden">Create</span>
              </button>
              <button
                onClick={() => navigate('/payouts')}
                className="px-4 md:px-6 py-2 bg-white border border-neutral-200 hover:bg-neutral-50 text-neutral-900 rounded-lg text-sm font-medium transition-colors"
              >
                Withdraw
              </button>
            </div>
          </div>


          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6 mb-6 md:mb-10">

            <div className="bg-white rounded-xl md:rounded-2xl p-5 md:p-7 border border-neutral-200 shadow-sm hover:shadow-md hover:border-neutral-300 transition-all duration-200">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-neutral-500 uppercase tracking-wide">Available</span>
                <div className="w-8 h-8 md:w-10 md:h-10 rounded-xl bg-emerald-50 flex items-center justify-center">
                  <svg className="w-4 h-4 md:w-5 md:h-5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
              <div className="text-2xl md:text-4xl font-semibold text-neutral-900 mb-2 tabular-nums lining-nums tracking-tight">
                {formatCurrency(availableBalance, balance?.currency)}
              </div>
              <p className="text-xs md:text-sm text-neutral-600 tracking-[-0.01em]">Ready to transfer</p>
            </div>


            <div className="bg-white rounded-xl md:rounded-2xl p-5 md:p-7 border border-neutral-200 shadow-sm hover:shadow-md hover:border-neutral-300 transition-all duration-200">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-neutral-500 uppercase tracking-wide">Pending</span>
                <div className="w-8 h-8 md:w-10 md:h-10 rounded-xl bg-amber-50 flex items-center justify-center">
                  <svg className="w-4 h-4 md:w-5 md:h-5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
              <div className="text-2xl md:text-4xl font-semibold text-neutral-900 mb-2 tabular-nums lining-nums tracking-tight">
                {formatCurrency(pendingBalance, balance?.currency)}
              </div>
              <p className="text-xs md:text-sm text-neutral-600 tracking-[-0.01em]">
                {charges.filter(c => c.status === 'pending').length} processing
              </p>
            </div>


            <div className="bg-white rounded-xl md:rounded-2xl p-5 md:p-7 border border-neutral-200 shadow-sm hover:shadow-md hover:border-neutral-300 transition-all duration-200">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-neutral-500 uppercase tracking-wide">Total</span>
                <div className="w-8 h-8 md:w-10 md:h-10 rounded-xl bg-blue-50 flex items-center justify-center">
                  <svg className="w-4 h-4 md:w-5 md:h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                  </svg>
                </div>
              </div>
              <div className="text-2xl md:text-4xl font-semibold text-neutral-900 mb-2 tabular-nums lining-nums tracking-tight">
                {formatCurrency(totalVolume, balance?.currency)}
              </div>
              <p className="text-xs md:text-sm text-neutral-600 tracking-[-0.01em]">{charges.length} charges</p>
            </div>
          </div>


          <div className="bg-white rounded-xl border border-neutral-200 shadow-sm mb-6 md:mb-8">
            <div className="px-4 md:px-6 py-3 md:py-4 border-b border-neutral-200 flex items-center justify-between">
              <h2 className="text-base md:text-lg font-bold text-neutral-900">Recent Transactions</h2>
              <Link to="/charges" className="text-xs md:text-sm text-neutral-600 hover:text-neutral-900 font-medium flex items-center gap-1">
                <span className="hidden sm:inline">View all</span>
                <span className="sm:hidden">All</span>
                <svg className="w-3 h-3 md:w-4 md:h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>
            </div>
            <div className="divide-y divide-neutral-100">
              {charges.length === 0 && payouts.length === 0 ? (
                <div className="px-4 md:px-6 py-8 md:py-12 text-center">
                  <div className="w-12 h-12 md:w-16 md:h-16 bg-neutral-100 rounded-full flex items-center justify-center mx-auto mb-3 md:mb-4">
                    <svg className="w-6 h-6 md:w-8 md:h-8 text-neutral-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <h3 className="text-base md:text-lg font-semibold text-neutral-900 mb-1 md:mb-2">No transactions yet</h3>
                  <p className="text-sm md:text-base text-neutral-600 mb-3 md:mb-4">Create your first charge to get started</p>
                  <button
                    onClick={() => setShowCreateCharge(true)}
                    className="btn-primary px-5 md:px-6 py-2 text-sm md:text-base"
                  >
                    Create Charge
                  </button>
                </div>
              ) : (
                [...charges, ...payouts].sort((a, b) => new Date(b.created_at) - new Date(a.created_at)).slice(0, 10).map((transaction) => (
                  <div key={transaction.id} className="px-4 md:px-6 py-3 md:py-4 hover:bg-neutral-50 transition-colors">
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-2 md:gap-4 flex-1 min-w-0">
                        <div className={`w-2 h-2 rounded-full flex-shrink-0 ${
                          transaction.status === 'succeeded' ? 'bg-emerald-500' :
                          transaction.status === 'pending' ? 'bg-amber-500' :
                          'bg-red-500'
                        }`} />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 md:gap-3 mb-0.5 md:mb-1">
                            <code className="text-xs md:text-sm font-mono font-medium text-neutral-900 truncate">{transaction.id}</code>
                            <span className={`px-1.5 md:px-2 py-0.5 rounded-full text-xs font-medium border ${getStatusStyles(transaction.status)}`}>
                              {transaction.status}
                            </span>
                          </div>
                          <p className="text-xs md:text-sm text-neutral-600 truncate">{renderTransactionTitle(transaction)}</p>
                          <p className="text-xs text-neutral-500 mt-0.5">{formatDate(transaction.created_at)}</p>
                        </div>
                      </div>
                      <div className="text-right flex-shrink-0">
                        <div className="text-base md:text-lg font-bold text-neutral-900 tabular-nums lining-nums">
                          {formatCurrency(transaction.amount, transaction.currency)}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>


          <div className="bg-white rounded-xl border border-neutral-200 shadow-sm">
            <div className="px-6 py-4 border-b border-neutral-200 flex items-center justify-between">
              <h2 className="text-lg font-bold text-neutral-900">API Keys</h2>
              <Link to="/api-keys" className="text-sm text-neutral-600 hover:text-neutral-900 font-medium flex items-center gap-1">
                Manage keys
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>
            </div>
            <div className="p-6">
              {apiKeys.length === 0 ? (
                <div className="text-center py-8">
                  <div className="w-12 h-12 bg-neutral-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                    <svg className="w-6 h-6 text-neutral-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                    </svg>
                  </div>
                  <p className="text-neutral-600 mb-4">No API keys yet. Create one to start making API calls.</p>
                  <Link to="/api-keys" className="btn-primary px-6 py-2 inline-block">
                    Create API Key
                  </Link>
                </div>
              ) : (
                <div className="space-y-3">
                  {apiKeys.slice(0, 3).map((key) => (
                    <div key={key.id} className="flex items-center justify-between p-4 bg-neutral-50 rounded-lg">
                      <div className="flex items-center gap-3 flex-1 min-w-0">
                        <div className="w-10 h-10 bg-neutral-900 rounded-lg flex items-center justify-center flex-shrink-0">
                          <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                          </svg>
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-neutral-900 mb-0.5">{key.name || 'Unnamed Key'}</div>
                          <div className="flex items-center gap-2 text-sm">
                            <code className="text-neutral-600 font-mono truncate">{key.key_prefix}••••••••</code>
                            <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                              key.environment === 'live' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'
                            }`}>
                              {key.environment}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
        {overlayActive && (
          <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-white/85 backdrop-blur-sm">
            <div className="max-w-md w-full mx-4 p-8 bg-white border border-neutral-200 rounded-2xl shadow-xl">
              <div className="mb-6 text-center">
                <div className="mx-auto w-14 h-14 bg-neutral-900 rounded-xl flex items-center justify-center mb-4">
                  <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h2 className="text-2xl font-bold text-neutral-900 mb-2">Verify Your Account</h2>
                <p className="text-neutral-600 text-sm">Please verify your business details before accessing core features like creating charges or managing API keys.</p>
              </div>
              <div className="space-y-4 text-sm text-neutral-700">
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-neutral-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p>Verification helps us protect your account and enable payouts and production API usage.</p>
                </div>
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-neutral-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                  </svg>
                  <p>Create test charges after verifying; production features unlock once completed.</p>
                </div>
              </div>
              <div className="mt-8 flex flex-col sm:flex-row gap-3">
                <button
                  onClick={goToVerify}
                  className="flex-1 px-6 py-3 bg-neutral-900 hover:bg-neutral-800 text-white rounded-xl font-semibold transition-all"
                >
                  Verify Now
                </button>
                <button
                  onClick={handleOverlayLogout}
                  className="px-6 py-3 bg-white border-2 border-neutral-300 hover:border-neutral-400 hover:bg-neutral-50 text-neutral-700 rounded-xl font-semibold transition-all"
                >
                  Log Out
                </button>
              </div>
              <p className="mt-4 text-xs text-neutral-500 text-center">You previously skipped verification. Complete it to continue.</p>
            </div>
          </div>
        )}
      </div>


      {showCreateCharge && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50 backdrop-blur-sm" onClick={() => setShowCreateCharge(false)}>
          <div className="bg-white rounded-2xl max-w-lg w-full shadow-2xl" onClick={(e) => e.stopPropagation()}>

            <div className="px-6 py-5 border-b border-neutral-200">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xl font-bold text-neutral-900">Create New Charge</h3>
                  <p className="text-sm text-neutral-600 mt-1">Process a payment from your customer</p>
                </div>
                <button
                  onClick={() => setShowCreateCharge(false)}
                  className="w-8 h-8 flex items-center justify-center rounded-lg text-neutral-400 hover:text-neutral-600 hover:bg-neutral-100 transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>


            {chargeError && (
              <div className="mx-6 mt-4 p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
                <svg className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <p className="text-sm text-red-800">{chargeError}</p>
              </div>
            )}


            <form onSubmit={handleCreateCharge} className="px-6 py-6 space-y-5">
              <div>
                <label className="block text-sm font-semibold text-neutral-700 mb-2">
                  Amount <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <div className="absolute left-4 top-1/2 -translate-y-1/2 text-neutral-500 font-medium">
                    {currencySymbols[chargeForm.currency] || chargeForm.currency}
                  </div>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    value={chargeForm.amount}
                    onChange={(e) => setChargeForm({ ...chargeForm, amount: e.target.value })}
                    className="w-full pl-10 pr-4 py-3 border border-neutral-300 rounded-xl focus:ring-2 focus:ring-neutral-900 focus:border-neutral-900 transition-all text-lg font-semibold"
                    placeholder="100.00"
                    required
                    disabled={creatingCharge}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-neutral-700 mb-2">
                  Currency <span className="text-red-500">*</span>
                </label>
                <select
                  value={chargeForm.currency}
                  onChange={(e) => setChargeForm({ ...chargeForm, currency: e.target.value })}
                  className="w-full px-4 py-3 border border-neutral-300 rounded-xl focus:ring-2 focus:ring-neutral-900 focus:border-neutral-900 transition-all font-medium"
                  disabled={creatingCharge}
                >
                  <option value="NGN">NGN - Nigerian Naira</option>
                  <option value="USD">USD - US Dollar</option>
                  <option value="EUR">EUR - Euro</option>
                  <option value="GBP">GBP - British Pound</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-neutral-700 mb-2">
                  Description <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={chargeForm.description}
                  onChange={(e) => setChargeForm({ ...chargeForm, description: e.target.value })}
                  className="w-full px-4 py-3 border border-neutral-300 rounded-xl focus:ring-2 focus:ring-neutral-900 focus:border-neutral-900 transition-all resize-none"
                  placeholder="E.g., Payment for services, Product purchase, Consultation fee"
                  rows="3"
                  required
                  disabled={creatingCharge}
                />
                <p className="mt-2 text-xs text-neutral-500">This will appear on the charge details and customer receipts</p>
              </div>


              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateCharge(false)}
                  className="flex-1 px-6 py-3 bg-white border-2 border-neutral-300 hover:border-neutral-400 hover:bg-neutral-50 text-neutral-700 rounded-xl font-semibold transition-all"
                  disabled={creatingCharge}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-6 py-3 bg-neutral-900 hover:bg-neutral-800 text-white rounded-xl font-semibold transition-all disabled:opacity-50 flex items-center justify-center gap-2 shadow-lg hover:shadow-xl"
                  disabled={creatingCharge}
                >
                  {creatingCharge ? (
                    <>
                      <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Processing...
                    </>
                  ) : (
                    <>
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                      Create Charge
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  )
}