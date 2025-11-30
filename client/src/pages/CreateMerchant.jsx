import { useState } from 'react'
import { api } from '../lib/apiClient'
import { useAuth } from '../context/AuthContext'

export default function CreateMerchant() {
  const { token } = useAuth()
  const [form, setForm] = useState({ currency: 'USD', settlement_schedule: 'daily' })
  const [loading,setLoading]=useState(false)
  const [error,setError]=useState(null)
  const [merchant,setMerchant]=useState(null)

  const submit = async (e) => {
    e.preventDefault(); setError(null); setLoading(true)
    try { const res = await api.createMerchant(token, form); setMerchant(res) }
    catch (err) { setError(err.detail || 'Creation failed') }
    finally { setLoading(false) }
  }

  return (
    <div className="max-w-xl">
      <h2 className="text-xl font-semibold mb-4">Create merchant account</h2>
      <form onSubmit={submit} className="space-y-4">
        {['currency','settlement_schedule'].map((k)=> (
          <div key={k}>
            <label className="block text-xs font-medium mb-1 capitalize">{k.replace('_',' ')}</label>
            <input value={form[k]} onChange={(e)=>setForm({ ...form, [k]: e.target.value })} className="w-full border border-neutral-300 rounded px-3 py-2 text-sm bg-white" />
          </div>
        ))}
        <button disabled={loading} className="w-full bg-neutral-900 text-white py-2 rounded text-sm font-medium disabled:opacity-50">{loading ? 'Creating...' : 'Create merchant'}</button>
        {error && <p className="text-red-600 text-xs">{error}</p>}
        {merchant && <p className="text-emerald-600 text-xs">Merchant created: {merchant.merchant_id}</p>}
      </form>
    </div>
  )
}

