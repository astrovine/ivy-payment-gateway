import { useEffect, useState } from 'react'
import Navbar from '../components/Navbar'
import { api } from '../lib/apiClient'

export default function AdminPayouts(){
  const [loading, setLoading] = useState(true)
  const [payouts, setPayouts] = useState([])
  const [error, setError] = useState('')

  const load = async () => {
    try{
      setLoading(true)
      const res = await api.adminListPayouts()
      setPayouts(res.payouts || [])
    }catch(e){
      setError(e.message || 'Failed to load payouts')
    }finally{
      setLoading(false)
    }
  }

  useEffect(()=>{ load() }, [])

  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-neutral-50 py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-2xl font-bold mb-4">Payouts</h1>
          {error && <div className="mb-4 text-red-700">{error}</div>}
          {loading ? (
            <div>Loading...</div>
          ) : (
            <div className="bg-white rounded-lg shadow p-4">
              <table className="w-full text-sm table-auto">
                <thead>
                  <tr className="text-left">
                    <th className="p-2">ID</th>
                    <th className="p-2">Merchant</th>
                    <th className="p-2">Amount</th>
                    <th className="p-2">Currency</th>
                    <th className="p-2">Status</th>
                    <th className="p-2">Created</th>
                  </tr>
                </thead>
                <tbody>
                  {payouts.map((p, idx) => (
                    <tr key={p.id ? `payout-${p.id}` : `payout-${idx}`} className="border-t">
                      <td className="p-2 font-mono">{p.id ?? '-'}</td>
                      <td className="p-2">{p.merchant_id ?? '-'}</td>
                      <td className="p-2">{p.amount ? Number(p.amount).toLocaleString() : '-'}</td>
                      <td className="p-2">{p.currency ?? '-'}</td>
                      <td className="p-2">{p.status ?? '-'}</td>
                      <td className="p-2">{p.created_at ? new Date(p.created_at).toLocaleString() : '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </>
  )
}
