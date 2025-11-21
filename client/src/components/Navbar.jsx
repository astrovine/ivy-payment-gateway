import { useState, useEffect } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { token, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [unreadCount, setUnreadCount] = useState(0)
  const [isAdmin, setIsAdmin] = useState(false)

  useEffect(() => {
    const checkAdmin = () => {
      const userRaw = localStorage.getItem('user')
      if (userRaw) {
        try {
          const user = JSON.parse(userRaw)
          setIsAdmin(!!user.is_superadmin)
        } catch {
          setIsAdmin(false)
        }
      }
    }
    checkAdmin()
    const fetchUnread = async () => {
      try {
        const res = await (await import('../lib/apiClient')).api.getUnreadNotificationsCount()
        setUnreadCount(res.unread || 0)
      } catch {
        setUnreadCount(0)
      }
    }
    fetchUnread()
    const unreadInterval = setInterval(fetchUnread, 60000)
    return () => clearInterval(unreadInterval)
  }, [location.pathname])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  useEffect(() => {
    setMobileMenuOpen(false)
  }, [location.pathname])

  useEffect(() => {
    if (mobileMenuOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }
    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [mobileMenuOpen])

  if (!token) return null

  const isActive = (path) => location.pathname === path

  return (
    <>
      <nav className="bg-white border-b border-neutral-200 sticky top-0 z-50 shadow-sm">
        <div className="w-full px-3 sm:px-4 md:px-6 lg:max-w-7xl lg:mx-auto">
          <div className="flex items-center justify-between h-16 md:h-[4.5rem]">

            <Link to="/dashboard" className="flex items-center gap-3 group">
              <div className="w-9 h-9 bg-neutral-900 rounded-xl flex items-center justify-center shadow-sm group-hover:shadow-md transition-shadow">
                <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707" />
                </svg>
              </div>
              <span className="text-xl font-semibold tracking-tight">Ivy</span>
            </Link>


            <div className="flex items-center gap-3">

              <div className="hidden md:flex items-center gap-1.5">
                {isAdmin ? (
                  <>
                    <Link
                      to="/admin"
                      className={`px-4 py-2.5 text-[15px] font-medium rounded-xl transition-all tracking-[-0.01em] ${
                        isActive('/admin') || location.pathname.startsWith('/admin/merchants')
                          ? 'bg-neutral-900 text-white shadow-sm'
                          : 'text-neutral-700 hover:text-neutral-900 hover:bg-neutral-100'
                      }`}
                    >
                      Dashboard
                    </Link>
                    <Link
                      to="/admin/transactions"
                      className={`px-4 py-2.5 text-[15px] font-medium rounded-xl transition-all tracking-[-0.01em] ${
                        isActive('/admin/transactions')
                          ? 'bg-neutral-900 text-white shadow-sm'
                          : 'text-neutral-700 hover:text-neutral-900 hover:bg-neutral-100'
                      }`}
                    >
                      Transactions
                    </Link>
                    <Link
                      to="/admin/audit-logs"
                      className={`px-4 py-2.5 text-[15px] font-medium rounded-xl transition-all tracking-[-0.01em] ${
                        isActive('/admin/audit-logs')
                          ? 'bg-neutral-900 text-white shadow-sm'
                          : 'text-neutral-700 hover:text-neutral-900 hover:bg-neutral-100'
                      }`}
                    >
                      Audit Logs
                    </Link>
                    <Link
                      to="/admin/payouts"
                      className={`px-4 py-2.5 text-[15px] font-medium rounded-xl transition-all tracking-[-0.01em] ${
                        isActive('/admin/payouts')
                          ? 'bg-neutral-900 text-white shadow-sm'
                          : 'text-neutral-700 hover:text-neutral-900 hover:bg-neutral-100'
                      }`}
                    >
                      Payouts
                    </Link>
                  </>
                ) : (
                  <>
                    <Link
                      to="/dashboard"
                      className={`px-4 py-2.5 text-[15px] font-medium rounded-xl transition-all tracking-[-0.01em] ${
                        isActive('/dashboard')
                          ? 'bg-neutral-900 text-white shadow-sm'
                          : 'text-neutral-700 hover:text-neutral-900 hover:bg-neutral-100'
                      }`}
                    >
                      Dashboard
                    </Link>
                    <Link
                      to="/charges"
                      className={`px-4 py-2.5 text-[15px] font-medium rounded-xl transition-all tracking-[-0.01em] ${
                        isActive('/charges')
                          ? 'bg-neutral-900 text-white shadow-sm'
                          : 'text-neutral-700 hover:text-neutral-900 hover:bg-neutral-100'
                      }`}
                    >
                      Payments
                    </Link>
                    <Link
                      to="/payouts"
                      className={`px-4 py-2.5 text-[15px] font-medium rounded-xl transition-all tracking-[-0.01em] ${
                        isActive('/payouts')
                          ? 'bg-neutral-900 text-white shadow-sm'
                          : 'text-neutral-700 hover:text-neutral-900 hover:bg-neutral-100'
                      }`}
                    >
                      Payouts
                    </Link>
                    <Link
                      to="/api-keys"
                      className={`px-4 py-2.5 text-[15px] font-medium rounded-xl transition-all tracking-[-0.01em] ${
                        isActive('/api-keys')
                          ? 'bg-neutral-900 text-white shadow-sm'
                          : 'text-neutral-700 hover:text-neutral-900 hover:bg-neutral-100'
                      }`}
                    >
                      API Keys
                    </Link>
                    <Link
                      to="/kyc"
                      className={`px-4 py-2.5 text-[15px] font-medium rounded-xl transition-all tracking-[-0.01em] ${
                        isActive('/kyc')
                          ? 'bg-neutral-900 text-white shadow-sm'
                          : 'text-neutral-700 hover:text-neutral-900 hover:bg-neutral-100'
                      }`}
                    >
                      KYC
                    </Link>
                    <Link
                      to="/analytics"
                      className={`px-4 py-2.5 text-[15px] font-medium rounded-xl transition-all tracking-[-0.01em] ${
                        isActive('/analytics')
                          ? 'bg-neutral-900 text-white shadow-sm'
                          : 'text-neutral-700 hover:text-neutral-900 hover:bg-neutral-100'
                      }`}
                    >
                      Analytics
                    </Link>
                    <Link
                      to="/settings"
                      className={`px-4 py-2.5 text-[15px] font-medium rounded-xl transition-all tracking-[-0.01em] ${
                        isActive('/settings')
                          ? 'bg-neutral-900 text-white shadow-sm'
                          : 'text-neutral-700 hover:text-neutral-900 hover:bg-neutral-100'
                      }`}
                    >
                      Settings
                    </Link>
                  </>
                )}
              </div>


              <div className="hidden md:flex items-center gap-3 pl-6 border-l border-neutral-200">
                <Link to="/notifications" className="relative">
                  <button className="p-2 rounded-full hover:bg-neutral-100">
                    <svg className="w-5 h-5 text-neutral-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118.6 14.6V11a6 6 0 10-12 0v3.6c0 .538-.214 1.055-.595 1.439L4 17h5" />
                    </svg>
                    {unreadCount > 0 && (
                      <span className="absolute -top-1 -right-1 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white bg-red-600 rounded-full">{unreadCount}</span>
                    )}
                  </button>
                </Link>
                <button
                  onClick={handleLogout}
                  className="px-4 py-2.5 text-[15px] font-medium text-neutral-700 hover:text-red-600 hover:bg-red-50 rounded-xl transition-all flex items-center gap-2 tracking-[-0.01em]"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                  Logout
                </button>
              </div>


              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="md:hidden p-2 rounded-xl hover:bg-neutral-100 transition-colors"
                aria-label="Toggle menu"
              >
                {mobileMenuOpen ? (
                  <svg className="w-6 h-6 text-neutral-900" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                ) : (
                  <svg className="w-6 h-6 text-neutral-900" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </div>
      </nav>


      {mobileMenuOpen && (
        <div className="fixed inset-0 z-40 md:hidden">

          <div
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            onClick={() => setMobileMenuOpen(false)}
          />


          <div className="absolute top-16 left-0 right-0 bg-white backdrop-blur-none border-b border-neutral-200 shadow-xl animate-slide-down">
            <div className="px-4 py-6 space-y-2 max-h-[calc(100vh-4rem)] overflow-y-auto">

              {isAdmin ? (
                <>
                  <Link
                    to="/admin"
                    className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                      isActive('/admin') || location.pathname.startsWith('/admin/merchants')
                        ? 'bg-neutral-900 text-white shadow-sm'
                        : 'text-neutral-700 hover:bg-neutral-100'
                    }`}
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                    <span className="font-medium text-[15px]">Dashboard</span>
                  </Link>

                  <Link
                    to="/admin/transactions"
                    className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                      isActive('/admin/transactions')
                        ? 'bg-neutral-900 text-white shadow-sm'
                        : 'text-neutral-700 hover:bg-neutral-100'
                    }`}
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                    </svg>
                    <span className="font-medium text-[15px]">Transactions</span>
                  </Link>

                  <Link
                    to="/admin/audit-logs"
                    className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                      isActive('/admin/audit-logs')
                        ? 'bg-neutral-900 text-white shadow-sm'
                        : 'text-neutral-700 hover:bg-neutral-100'
                    }`}
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <span className="font-medium text-[15px]">Audit Logs</span>
                  </Link>

                  <Link
                    to="/admin/payouts"
                    className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                      isActive('/admin/payouts')
                        ? 'bg-neutral-900 text-white shadow-sm'
                        : 'text-neutral-700 hover:bg-neutral-100'
                    }`}
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                    </svg>
                    <span className="font-medium text-[15px]">Payouts</span>
                  </Link>
                </>
              ) : (
                <>
                  <Link
                    to="/dashboard"
                    className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                      isActive('/dashboard')
                        ? 'bg-neutral-900 text-white shadow-sm'
                        : 'text-neutral-700 hover:bg-neutral-100'
                    }`}
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                    </svg>
                    <span className="font-medium text-[15px]">Dashboard</span>
                  </Link>

                  <Link
                    to="/charges"
                    className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                      isActive('/charges')
                        ? 'bg-neutral-900 text-white shadow-sm'
                        : 'text-neutral-700 hover:bg-neutral-100'
                    }`}
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                    </svg>
                    <span className="font-medium text-[15px]">Payments</span>
                  </Link>

                  <Link
                    to="/payouts"
                    className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                      isActive('/payouts')
                        ? 'bg-neutral-900 text-white shadow-sm'
                        : 'text-neutral-700 hover:bg-neutral-100'
                    }`}
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                    </svg>
                    <span className="font-medium text-[15px]">Payouts</span>
                  </Link>

                  <Link
                    to="/api-keys"
                    className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                      isActive('/api-keys')
                        ? 'bg-neutral-900 text-white shadow-sm'
                        : 'text-neutral-700 hover:bg-neutral-100'
                    }`}
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                    </svg>
                    <span className="font-medium text-[15px]">API Keys</span>
                  </Link>

                  <Link
                    to="/kyc"
                    className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                      isActive('/kyc')
                        ? 'bg-neutral-900 text-white shadow-sm'
                        : 'text-neutral-700 hover:bg-neutral-100'
                    }`}
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                    <span className="font-medium text-[15px]">KYC</span>
                  </Link>

                  <Link
                    to="/notifications"
                    className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                      isActive('/notifications')
                        ? 'bg-neutral-900 text-white shadow-sm'
                        : 'text-neutral-700 hover:bg-neutral-100'
                    }`}
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118.6 14.6V11a6 6 0 10-12 0v3.6c0 .538-.214 1.055-.595 1.439L4 17h5" />
                    </svg>
                    <span className="font-medium text-[15px]">Notifications</span>
                  </Link>

                  <Link
                    to="/analytics"
                    className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                      isActive('/analytics')
                        ? 'bg-neutral-900 text-white shadow-sm'
                        : 'text-neutral-700 hover:bg-neutral-100'
                    }`}
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    <span className="font-medium text-[15px]">Analytics</span>
                  </Link>

                  <Link
                    to="/settings"
                    className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                      isActive('/settings')
                        ? 'bg-neutral-900 text-white shadow-sm'
                        : 'text-neutral-700 hover:bg-neutral-100'
                    }`}
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    <span className="font-medium text-[15px]">Settings</span>
                  </Link>
                </>
              )}


              <div className="pt-4 mt-4 border-t border-neutral-200">
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-red-600 hover:bg-red-50 transition-all"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                  <span className="font-medium text-[15px]">Logout</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
