import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import { api } from '../lib/apiClient'

export default function APIKeys() {
  const navigate = useNavigate()
  const [keys, setKeys] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState('')
  const [newKeyData, setNewKeyData] = useState(null)

  const [form, setForm] = useState({
    name: '',
    key_type: 'secret',
    environment: 'test'
  })

  const [revoking, setRevoking] = useState(null)
  const [showRevokeConfirm, setShowRevokeConfirm] = useState(null)
  const [revokeReason, setRevokeReason] = useState('')

  const [rolling, setRolling] = useState(null)
  const [showRollConfirm, setShowRollConfirm] = useState(null)
  const [rolledKeyData, setRolledKeyData] = useState(null)

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      navigate('/login')
      return
    }
    loadKeys()
  }, [navigate])

  const loadKeys = async () => {
    try {
      setLoading(true)
      const data = await api.getAPIKeys()
      const keysArray = Array.isArray(data) ? data : data?.api_keys || []
      setKeys(keysArray)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const createKey = async (e) => {
    e.preventDefault()
    setError('')
    if (!form.name.trim()) {
      setError('Please enter a key name')
      return
    }
    try {
      setCreating(true)
      const response = await api.createAPIKey(form)
      setNewKeyData(response)
      setForm({ name: '', key_type: 'secret', environment: 'test' })
      await loadKeys()
    } catch (err) {
      setError(err.message || 'Failed to create API key')
    } finally {
      setCreating(false)
    }
  }

  const revokeKey = async (keyId) => {
    try {
      setRevoking(keyId)
      await api.revokeAPIKey(keyId, revokeReason || undefined)
      setKeys(keys.filter(k => k.id !== keyId))
      setShowRevokeConfirm(null)
      setRevokeReason('')
    } catch (err) {
      setError(err.message || 'Failed to revoke API key')
    } finally {
      setRevoking(null)
    }
  }

  const rollKey = async (keyId) => {
    try {
      setRolling(keyId)
      const response = await api.rollAPIKey(keyId)
      setRolledKeyData(response) 
      setShowRollConfirm(null)
      await loadKeys()
    } catch (err) {
      setError(err.message || 'Failed to roll API key')
    } finally {
      setRolling(null)
    }
  }

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
    alert('Copied to clipboard!')
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric', month: 'short', day: 'numeric'
    })
  }

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="min-h-screen bg-neutral-50 flex items-center justify-center">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-neutral-900 mb-4"></div>
            <p className="text-neutral-600">Loading API keys...</p>
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
          
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-6">
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-neutral-900 mb-2">API Keys</h1>
              <p className="text-sm md:text-base text-neutral-600 max-w-2xl">
                Manage your API keys to authenticate requests to the Ivy API. Keep your secret keys secure and never share them publicly.
              </p>
            </div>
            <button
              onClick={() => setShowCreate(true)}
              className="btn-primary px-4 md:px-6 py-2 md:py-3 flex items-center justify-center gap-2 text-sm md:text-base whitespace-nowrap"
            >
              <svg className="w-4 h-4 md:w-5 md:h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
              </svg>
              Create API Key
            </button>
          </div>

          
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 md:p-5 mb-6 flex items-start gap-3">
            <svg className="w-5 h-5 md:w-6 md:h-6 text-blue-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            <div className="flex-1">
              <h3 className="text-sm md:text-base font-semibold text-blue-900 mb-1">Keep your keys secure</h3>
              <p className="text-xs md:text-sm text-blue-800">
                Your secret keys can be used to make API requests. Never commit them to version control or share them publicly.
              </p>
            </div>
          </div>

          
          <div className="bg-white rounded-xl border border-neutral-200 shadow-sm overflow-hidden">
            <div className="px-4 md:px-6 py-4 border-b border-neutral-200">
              <h2 className="text-lg font-bold text-neutral-900">Your API Keys</h2>
            </div>

            {keys.length === 0 ? (
              <div className="px-4 md:px-6 py-12 md:py-16 text-center">
                <div className="w-16 h-16 bg-neutral-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-neutral-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-neutral-900 mb-2">No API keys yet</h3>
                <p className="text-neutral-600 mb-6 max-w-md mx-auto">
                  Create your first API key to start making requests to the Ivy API
                </p>
                <button
                  onClick={() => setShowCreate(true)}
                  className="btn-primary px-6 py-2"
                >
                  Create API Key
                </button>
              </div>
            ) : (
              <div className="divide-y divide-neutral-100">
                {keys.map((key) => (
                  <div key={key.id} className="px-4 md:px-6 py-4 md:py-5 hover:bg-neutral-50 transition-colors">
                    <div className="flex flex-col md:flex-row md:items-center gap-3 md:gap-4">
                      
                      <div className="hidden md:flex w-12 h-12 bg-neutral-900 rounded-xl items-center justify-center flex-shrink-0">
                        <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                        </svg>
                      </div>

                      
                      <div className="flex-1 min-w-0">
                        <div className="flex flex-wrap items-center gap-2 mb-2">
                          <h3 className="text-base md:text-lg font-semibold text-neutral-900">{key.name || 'Unnamed Key'}</h3>
                          <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                            key.environment === 'live' 
                              ? 'bg-emerald-100 text-emerald-700' 
                              : 'bg-amber-100 text-amber-700'
                          }`}>
                            {key.environment}
                          </span>
                          <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-neutral-100 text-neutral-700">
                            {key.key_type}
                          </span>
                          {!key.is_active && (
                            <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-700">revoked</span>
                          )}
                        </div>

                        <div className="flex items-center gap-2 mb-2">
                          <code className="text-sm font-mono text-neutral-600 bg-neutral-100 px-3 py-1 rounded-lg">
                            {key.key_prefix}••••••••••••••••
                          </code>
                          <button
                            onClick={() => copyToClipboard(key.key_prefix + '••••••••••••••••')}
                            className="p-1.5 text-neutral-500 hover:text-neutral-900 hover:bg-neutral-200 rounded transition-colors"
                            title="Copy"
                          >
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                            </svg>
                          </button>
                        </div>

                        <p className="text-xs md:text-sm text-neutral-500">
                          Created {formatDate(key.created_at)}{key.last_used_at ? ` · Last used ${formatDate(key.last_used_at)}` : ''}
                        </p>
                      </div>

                      
                      <div className="flex items-center gap-2 md:gap-3">
                        <button
                          onClick={() => setShowRollConfirm(key.id)}
                          disabled={rolling === key.id || !key.is_active}
                          className="px-3 md:px-4 py-2 text-sm font-medium text-neutral-600 hover:text-neutral-900 hover:bg-neutral-100 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {rolling === key.id ? 'Rolling...' : 'Roll'}
                        </button>
                        <button
                          onClick={() => setShowRevokeConfirm(key.id)}
                          disabled={revoking === key.id || !key.is_active}
                          className="px-3 md:px-4 py-2 text-sm font-medium text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {revoking === key.id ? 'Revoking...' : 'Revoke'}
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      
      {showCreate && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50 backdrop-blur-sm" onClick={() => !newKeyData && setShowCreate(false)}>
          <div className="bg-white rounded-2xl max-w-lg w-full shadow-2xl" onClick={(e) => e.stopPropagation()}>
            {!newKeyData ? (
              <>
                <div className="px-6 py-5 border-b border-neutral-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-xl font-bold text-neutral-900">Create API Key</h3>
                      <p className="text-sm text-neutral-600 mt-1">Generate a new API key for your application</p>
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

                <form onSubmit={createKey} className="px-6 py-6 space-y-5">
                  <div>
                    <label className="block text-sm font-semibold text-neutral-700 mb-2">
                      Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={form.name}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
                      className="w-full px-4 py-3 border border-neutral-300 rounded-xl focus:ring-2 focus:ring-neutral-900 focus:border-neutral-900 transition-all font-medium"
                      placeholder="e.g., Production Server, Mobile App"
                      required
                      disabled={creating}
                    />
                    <p className="mt-2 text-xs text-neutral-500">Choose a descriptive name to identify this key</p>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-neutral-700 mb-2">
                      Key Type <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={form.key_type}
                      onChange={(e) => setForm({ ...form, key_type: e.target.value })}
                      className="w-full px-4 py-3 border border-neutral-300 rounded-xl focus:ring-2 focus:ring-neutral-900 focus:border-neutral-900 transition-all font-medium"
                      disabled={creating}
                    >
                      <option value="secret">Secret Key (for server-side)</option>
                      <option value="publishable">Publishable Key (for client-side)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-neutral-700 mb-2">
                      Environment <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={form.environment}
                      onChange={(e) => setForm({ ...form, environment: e.target.value })}
                      className="w-full px-4 py-3 border border-neutral-300 rounded-xl focus:ring-2 focus:ring-neutral-900 focus:border-neutral-900 transition-all font-medium"
                      disabled={creating}
                    >
                      <option value="test">Test (for development)</option>
                      <option value="live">Live (for production)</option>
                    </select>
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
                          Creating...
                        </>
                      ) : 'Create Key'}
                    </button>
                  </div>
                </form>
              </>
            ) : (
              <>
                <div className="px-6 py-5 border-b border-neutral-200 bg-emerald-50">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-emerald-600 rounded-full flex items-center justify-center">
                      <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-emerald-900">API Key Created!</h3>
                      <p className="text-sm text-emerald-700 mt-0.5">Save this key now - you won't see it again</p>
                    </div>
                  </div>
                </div>

                <div className="px-6 py-6">
                  <div className="bg-neutral-900 rounded-xl p-4 mb-4">
                    <div className="flex items-center justify-between gap-3 mb-2">
                      <span className="text-xs font-medium text-neutral-400 uppercase">Your API Key</span>
                      <button
                        onClick={() => copyToClipboard(newKeyData.api_key || newKeyData.key)}
                        className="px-3 py-1.5 bg-neutral-800 hover:bg-neutral-700 text-white text-xs font-medium rounded-lg transition-colors flex items-center gap-2"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                        Copy
                      </button>
                    </div>
                    <code className="text-sm font-mono text-emerald-400 break-all">
                      {newKeyData.api_key || newKeyData.key}
                    </code>
                  </div>

                  <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-6">
                    <div className="flex gap-3">
                      <svg className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                      <div className="flex-1">
                        <h4 className="text-sm font-semibold text-amber-900 mb-1">Important!</h4>
                        <p className="text-xs text-amber-800">
                          Make sure to copy your API key now. You won't be able to see it again!
                        </p>
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => { setNewKeyData(null); setShowCreate(false) }}
                    className="w-full px-6 py-3 bg-neutral-900 hover:bg-neutral-800 text-white rounded-xl font-semibold transition-all"
                  >
                    Done
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      
      {rolledKeyData && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50 backdrop-blur-sm" onClick={() => setRolledKeyData(null)}>
          <div className="bg-white rounded-2xl max-w-lg w-full shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="px-6 py-5 border-b border-neutral-200 bg-blue-50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
                  <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-xl font-bold text-blue-900">API Key Rolled</h3>
                  <p className="text-sm text-blue-700 mt-0.5">Your new key is shown below. Store it securely.</p>
                </div>
              </div>
            </div>
            <div className="px-6 py-6">
              <div className="bg-neutral-900 rounded-xl p-4 mb-4">
                <div className="flex items-center justify-between gap-3 mb-2">
                  <span className="text-xs font-medium text-neutral-400 uppercase">New API Key</span>
                  <button
                    onClick={() => copyToClipboard(rolledKeyData.api_key)}
                    className="px-3 py-1.5 bg-neutral-800 hover:bg-neutral-700 text-white text-xs font-medium rounded-lg transition-colors flex items-center gap-2"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    Copy
                  </button>
                </div>
                <code className="text-sm font-mono text-blue-400 break-all">{rolledKeyData.api_key}</code>
              </div>
              <button
                onClick={() => setRolledKeyData(null)}
                className="w-full px-6 py-3 bg-neutral-900 hover:bg-neutral-800 text-white rounded-xl font-semibold transition-all"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}

      
      {showRollConfirm && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50 backdrop-blur-sm" onClick={() => setShowRollConfirm(null)}>
          <div className="bg-white rounded-2xl max-w-md w-full shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="px-6 py-5 border-b border-neutral-200">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xl font-bold text-neutral-900">Roll API Key</h3>
                  <p className="text-sm text-neutral-600 mt-1">This will revoke the old key and create a new one</p>
                </div>
                <button
                  onClick={() => setShowRollConfirm(null)}
                  className="w-8 h-8 flex items-center justify-center rounded-lg text-neutral-400 hover:text-neutral-600 hover:bg-neutral-100 transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            <div className="px-6 py-6">
              <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6">
                <div className="flex gap-3">
                  <svg className="w-6 h-6 text-blue-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M12 20a8 8 0 100-16 8 8 0 000 16z" />
                  </svg>
                  <div>
                    <h4 className="text-sm font-bold text-blue-900 mb-2">Heads up:</h4>
                    <p className="text-sm text-blue-800">Rolling a key immediately revokes the old key. Any services using it must be updated to use the new key.</p>
                  </div>
                </div>
              </div>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowRollConfirm(null)}
                  className="flex-1 px-6 py-3 bg-white border-2 border-neutral-300 hover:border-neutral-400 hover:bg-neutral-50 text-neutral-700 rounded-xl font-semibold transition-all"
                  disabled={rolling}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => rollKey(showRollConfirm)}
                  className="flex-1 px-6 py-3 bg-neutral-900 hover:bg-neutral-800 text-white rounded-xl font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  disabled={rolling}
                >
                  {rolling ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      <span>Rolling...</span>
                    </>
                  ) : 'Roll Key'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      
      {showRevokeConfirm && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50 backdrop-blur-sm" onClick={() => setShowRevokeConfirm(null)}>
          <div className="bg-white rounded-2xl max-w-md w-full shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="px-6 py-5 border-b border-neutral-200">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xl font-bold text-red-600">Revoke API Key</h3>
                  <p className="text-sm text-neutral-600 mt-1">This action cannot be undone</p>
                </div>
                <button
                  onClick={() => setShowRevokeConfirm(null)}
                  className="w-8 h-8 flex items-center justify-center rounded-lg text-neutral-400 hover:text-neutral-600 hover:bg-neutral-100 transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            <div className="px-6 py-6">
              <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6">
                <div className="flex gap-3">
                  <svg className="w-6 h-6 text-red-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <div>
                    <h4 className="text-sm font-bold text-red-900 mb-2">Warning:</h4>
                    <p className="text-sm text-red-800">
                      Revoking this API key will immediately stop all requests using this key. Applications using this key will lose access.
                    </p>
                  </div>
                </div>
              </div>

              <label className="block text-sm font-semibold text-neutral-700 mb-2">Reason (optional)</label>
              <input
                type="text"
                value={revokeReason}
                onChange={(e) => setRevokeReason(e.target.value)}
                placeholder="e.g., key compromised, rotating keys"
                className="w-full mb-6 px-4 py-3 border border-neutral-300 rounded-xl focus:ring-2 focus:ring-neutral-900 focus:border-neutral-900 transition-all"
                disabled={revoking}
              />

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowRevokeConfirm(null)}
                  className="flex-1 px-6 py-3 bg-white border-2 border-neutral-300 hover:border-neutral-400 hover:bg-neutral-50 text-neutral-700 rounded-xl font-semibold transition-all"
                  disabled={revoking}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => revokeKey(showRevokeConfirm)}
                  className="flex-1 px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-xl font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  disabled={revoking}
                >
                  {revoking ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      <span>Revoking...</span>
                    </>
                  ) : (
                    'Revoke Key'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

