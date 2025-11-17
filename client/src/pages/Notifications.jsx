import { useEffect, useState } from 'react'
import { api } from '../lib/apiClient'
import { Link } from 'react-router-dom'
import Navbar from '../components/Navbar'

export default function Notifications() {
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading] = useState(true)
  const [pageError, setPageError] = useState('')

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.getNotifications(0, 50)
        setNotifications(Array.isArray(res) ? res : (res || []))
      } catch (err) {
        console.error('Failed to load notifications', err)
        setPageError(err?.message || 'Failed to load notifications')
        setNotifications([])
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const markRead = async (id) => {
    try {
      await api.markNotificationRead(id)
      setNotifications((prev) => prev.map(n => n.id === id ? { ...n, is_read: true, updated_at: new Date().toISOString() } : n))
    } catch (e) {
      console.error('Failed to mark notification read', e)
    }
  }

  return (
    <>
      <Navbar />

      <div className="min-h-screen bg-neutral-50">
        <div className="w-full px-3 sm:px-4 md:px-6 lg:max-w-4xl lg:mx-auto py-4 md:py-6 lg:py-8">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-2xl md:text-3xl font-bold text-neutral-900">Notifications</h1>
            <Link to="/settings" className="text-sm font-medium text-neutral-600 hover:text-neutral-900">
              Settings
            </Link>
          </div>

          {loading ? (
            <div className="text-center py-12 text-neutral-500">Loading...</div>
          ) : (
            <div className="bg-white rounded-xl border border-neutral-200 shadow-sm">
              {pageError && (
                <div className="p-4 text-sm text-red-700 bg-red-50 border border-red-100">{pageError}</div>
              )}
              <ul role="list" className="divide-y divide-neutral-200">
                {notifications.length === 0 && !pageError && (
                  <li className="p-6 text-center text-neutral-500">You have no new notifications.</li>
                )}
                {notifications.map(n => {
                  const created = n.created_at ? new Date(n.created_at) : null
                  const timeStr = created ? created.toLocaleString() : ''
                  return (
                    <li key={n.id} className={`p-4 sm:p-6 ${n.is_read ? 'opacity-70' : 'font-medium'}`}>
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="text-sm font-semibold text-neutral-900">{n.type}</div>
                          <div className="text-neutral-700 mt-1">{n.message}</div>
                          {n.data && <div className="text-xs text-neutral-500 mt-2 break-words">{n.data}</div>}
                          {timeStr && <div className="text-xs text-neutral-400 mt-2">{timeStr}</div>}
                        </div>
                        <div className="text-sm text-neutral-500 whitespace-nowrap pl-4">
                          {!n.is_read && (
                            <button onClick={() => markRead(n.id)} className="text-blue-600 font-medium hover:underline">Mark read</button>
                          )}
                        </div>
                      </div>
                    </li>
                  )
                })}
              </ul>
            </div>
          )}
        </div>
      </div>
    </>
  )
}