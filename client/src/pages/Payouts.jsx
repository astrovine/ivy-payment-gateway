import { useState, useEffect } from 'react'
import Navbar from '../components/Navbar'
import { api } from '../lib/apiClient'

export default function Payouts() {
  const [loading, setLoading] = useState(true)
  const [payouts, setPayouts] = useState([])
  const [accounts, setAccounts] = useState([])
  const [balance, setBalance] = useState({ available_balance: 0, currency: 'NGN' })
  const [showModal, setShowModal] = useState(false)
  const [form, setForm] = useState({ amount: '', payout_account_id: '' })
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const loadData = async () => {
    try {
      setLoading(true)
      const [p, a, b] = await Promise.all([api.getPayouts(), api.getPayoutAccounts(), api.getMerchantBalance()])
      setPayouts(p || [])
      setAccounts(a || [])
      setBalance(b || { available_balance: 0, currency: 'NGN' })
    } catch (err) {
      setError(err.message || 'Failed to load payouts')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const openModal = () => {
    setForm({ amount: '', payout_account_id: accounts[0]?.id || '' })
    setShowModal(true)
    setError('')
    setSuccess('')
  }

  const createPayout = async () => {
    setError('')
    setSuccess('')
    if (!form.amount || Number(form.amount) <= 0) {
      setError('Enter a valid amount')
      return
    }
    if (!form.payout_account_id) {
      setError('Select a destination account')
      return
    }
    if (Number(form.amount) > Number(balance.available_balance)) {
      setError('Amount exceeds available balance')
      return
    }
    setSubmitting(true)
    try {
      const payload = { amount: form.amount, currency: balance.currency, payout_account_id: form.payout_account_id }
      await api.createPayout(payload)
      setSuccess('Payout requested')
      setShowModal(false)
      await loadData()
    } catch (err) {
      setError(err.message || 'Failed to create payout')
    } finally {
      setSubmitting(false)
    }
  }

  const cancel = async (payoutId) => {
    if (!confirm('Cancel this payout?')) return
    try {
      await api.cancelPayout(payoutId)
      await loadData()
    } catch (err) {
      alert(err.message || 'Failed to cancel')
    }
  }

  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-neutral-50">
        <div className="max-w-5xl mx-auto px-4 md:px-6 py-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-bold">Payouts</h1>
              <p className="text-sm text-neutral-600">Request withdrawals and view your payout history</p>
            </div>
            <div>
              <button onClick={openModal} className="px-4 py-2 bg-neutral-900 text-white rounded-lg">Request Payout</button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-white rounded-xl p-4 border">
              <div className="text-sm text-neutral-500">Available balance</div>
              <div className="text-xl font-semibold mt-1">{Number(balance.available_balance).toLocaleString()} {balance.currency}</div>
            </div>
            <div className="bg-white rounded-xl p-4 border">
              <div className="text-sm text-neutral-500">Pending</div>
              <div className="text-xl font-semibold mt-1">{payouts.filter(p => p.status === 'pending').length}</div>
            </div>
            <div className="bg-white rounded-xl p-4 border">
              <div className="text-sm text-neutral-500">Destination accounts</div>
              <div className="text-xl font-semibold mt-1">{accounts.length}</div>
            </div>
          </div>

          {error && <div className="mb-4 p-3 bg-red-50 text-red-700 rounded">{error}</div>}
          {success && <div className="mb-4 p-3 bg-emerald-50 text-emerald-700 rounded">{success}</div>}

          <div className="bg-white rounded-xl border overflow-x-auto">
            <table className="w-full text-left divide-y">
              <thead>
                <tr className="text-sm text-neutral-600">
                  <th className="p-4">Date</th>
                  <th className="p-4">Amount</th>
                  <th className="p-4">Status</th>
                  <th className="p-4">Destination</th>
                  <th className="p-4">Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td className="p-6" colSpan={5}>Loading...</td></tr>
                ) : payouts.length === 0 ? (
                  <tr><td className="p-6" colSpan={5}>No payouts yet</td></tr>
                ) : (
                  payouts.map(p => (
                    <tr key={p.id} className="border-t">
                      <td className="p-4 text-sm">{new Date(p.created_at).toLocaleString()}</td>
                      <td className="p-4 text-sm">{Number(p.amount).toLocaleString()} {p.currency}</td>
                      <td className="p-4 text-sm">
                        {p.status === 'pending' && <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded">Pending</span>}
                        {p.status === 'succeeded' && <span className="px-2 py-1 bg-emerald-100 text-emerald-800 rounded">Processed</span>}
                        {p.status === 'failed' && <span className="px-2 py-1 bg-red-100 text-red-800 rounded">Failed</span>}
                      </td>
                      <td className="p-4 text-sm">{accounts.find(a => a.id === p.payout_account_id)?.bank_name || p.payout_account_id}</td>
                      <td className="p-4 text-sm flex gap-2">
                        <button onClick={() => alert(JSON.stringify(p, null, 2))} className="px-3 py-1 bg-neutral-100 rounded">View</button>
                        {p.status === 'pending' && <button onClick={() => cancel(p.id)} className="px-3 py-1 bg-red-50 text-red-700 rounded">Cancel</button>}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center">
          <div className="bg-white rounded-2xl w-full max-w-md p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Request Payout</h3>
              <button onClick={() => setShowModal(false)} className="text-neutral-500">Close</button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold mb-1">Amount ({balance.currency})</label>
                <input type="number" value={form.amount} onChange={(e) => setForm({...form, amount: e.target.value})} className="w-full px-4 py-2 border rounded" />
              </div>
              <div>
                <label className="block text-sm font-semibold mb-1">Destination account</label>
                <select value={form.payout_account_id} onChange={(e) => setForm({...form, payout_account_id: Number(e.target.value)})} className="w-full px-4 py-2 border rounded">
                  <option value="">Choose account</option>
                  {accounts.map(a => <option key={a.id} value={a.id}>{a.bank_name} - {a.account_number_last4}</option>)}
                </select>
              </div>
              <div className="flex justify-end gap-2">
                <button onClick={() => setShowModal(false)} className="px-4 py-2 border rounded">Cancel</button>
                <button onClick={createPayout} disabled={submitting} className="px-4 py-2 bg-neutral-900 text-white rounded">Submit</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
