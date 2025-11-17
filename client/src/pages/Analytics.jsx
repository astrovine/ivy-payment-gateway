import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/apiClient'

export default function Analytics() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [timeRange, setTimeRange] = useState('7d')
  const [chartData, setChartData] = useState([])
  const [balanceData, setBalanceData] = useState(null)
  const [transactions, setTransactions] = useState([])

  const loadAnalyticsData = useCallback(async () => {
    try {
      setLoading(true)

      const balance = await api.getMerchantBalance()
      setBalanceData(balance)

      const txResponse = await api.getCharges()
      const charges = Array.isArray(txResponse) ? txResponse : txResponse.charges || []

      setTransactions(charges)

      const processedData = processChargesIntoChartData(charges, timeRange)
      setChartData(processedData)

    } catch {
      setChartData([])
    } finally {
      setLoading(false)
    }
  }, [timeRange])

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      navigate('/login')
      return
    }
    loadAnalyticsData()
  }, [navigate, loadAnalyticsData])

  const processChargesIntoChartData = (charges, range) => {
    const days = range === '7d' ? 7 : range === '30d' ? 30 : 90
    const now = new Date()
    const data = []

    for (let i = days - 1; i >= 0; i--) {
      const date = new Date(now)
      date.setDate(date.getDate() - i)
      const dateStr = date.toISOString().split('T')[0]

      const dayCharges = charges.filter(charge => {
        const chargeDate = new Date(charge.created_at).toISOString().split('T')[0]
        return chargeDate === dateStr
      })

      const revenue = dayCharges
        .filter(c => c.status === 'succeeded')
        .reduce((sum, c) => sum + parseFloat(c.amount || 0), 0)

      const refunds = dayCharges
        .filter(c => c.status === 'refunded')
        .reduce((sum, c) => sum + parseFloat(c.amount || 0), 0)

      const failed = dayCharges.filter(c => c.status === 'failed').length
      const succeeded = dayCharges.filter(c => c.status === 'succeeded').length

      data.push({
        label: range === '7d' ? ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][date.getDay()] : `${date.getDate()}`,
        fullDate: dateStr,
        revenue: revenue,
        transactions: dayCharges.length,
        refunds: refunds,
        failed: failed,
        succeeded: succeeded,
        successRate: dayCharges.length > 0 ? (succeeded / dayCharges.length) * 100 : 0
      })
    }

    return data
  }


  const rawMaxValue = chartData.length > 0 ? Math.max(...chartData.map(d => d.revenue || 0)) : 100
  const maxValue = rawMaxValue > 0 ? rawMaxValue : 1

  const allZero = chartData.length > 0 && chartData.every(d => (d.revenue || 0) === 0)

  const formatCurrency = (amount) => {
    const currency = balanceData?.currency || 'USD'
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency
    }).format(amount || 0)
  }

  const totalRevenue = chartData.reduce((sum, d) => sum + (d.revenue || 0), 0)
  const totalTransactions = chartData.reduce((sum, d) => sum + (d.transactions || 0), 0)
  const avgTransaction = totalTransactions > 0 ? totalRevenue / totalTransactions : 0

  const displayBalance = balanceData ? {
    available: parseFloat(balanceData.available_balance || 0),
    pending: parseFloat(balanceData.pending_balance || 0),
    total: parseFloat(balanceData.available_balance || 0) + parseFloat(balanceData.pending_balance || 0)
  } : {
    available: 0,
    pending: 0,
    total: 0
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-neutral-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-neutral-900" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-neutral-50">

      <div className="bg-white border-b border-neutral-200">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-neutral-900">Analytics & Reports</h1>
              <p className="text-neutral-600 mt-1">Visualize your payment data and trends</p>
            </div>
            <button
              onClick={() => navigate('/dashboard')}
              className="px-4 py-2 border border-neutral-300 rounded-lg font-medium hover:bg-neutral-50 transition-colors"
            >
              ← Back to Dashboard
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">

        <div className="flex items-center gap-2 mb-8">
          <button
            onClick={() => setTimeRange('7d')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors tabular-nums lining-nums ${
              timeRange === '7d'
                ? 'bg-neutral-900 text-white'
                : 'bg-white border border-neutral-300 text-neutral-700 hover:bg-neutral-50'
            }`}
          >
            Last 7 days
          </button>
          <button
            onClick={() => setTimeRange('30d')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors tabular-nums lining-nums ${
              timeRange === '30d'
                ? 'bg-neutral-900 text-white'
                : 'bg-white border border-neutral-300 text-neutral-700 hover:bg-neutral-50'
            }`}
          >
            Last 30 days
          </button>
          <button
            onClick={() => setTimeRange('90d')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors tabular-nums lining-nums ${
              timeRange === '90d'
                ? 'bg-neutral-900 text-white'
                : 'bg-white border border-neutral-300 text-neutral-700 hover:bg-neutral-50'
            }`}
          >
            Last 90 days
          </button>
        </div>


        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-xl p-6 border border-neutral-200">
            <div className="text-sm text-neutral-600 mb-2">Total Revenue ({timeRange})</div>
            <div className="text-3xl font-bold text-neutral-900 mb-1 tabular-nums lining-nums">{formatCurrency(totalRevenue)}</div>
            <div className="text-sm text-emerald-600 font-medium tabular-nums">
              {balanceData ? `Available: ${formatCurrency(displayBalance.available)}` : 'Loading...'}
            </div>
          </div>
          <div className="bg-white rounded-xl p-6 border border-neutral-200">
            <div className="text-sm text-neutral-600 mb-2">Total Transactions</div>
            <div className="text-3xl font-bold text-neutral-900 mb-1 tabular-nums lining-nums">{totalTransactions.toLocaleString()}</div>
            <div className="text-sm text-neutral-600">
              {transactions.length > 0 ? `${transactions.length} charges processed` : 'No data yet'}
            </div>
          </div>
          <div className="bg-white rounded-xl p-6 border border-neutral-200">
            <div className="text-sm text-neutral-600 mb-2">Avg Transaction</div>
            <div className="text-3xl font-bold text-neutral-900 mb-1 tabular-nums lining-nums">{formatCurrency(avgTransaction)}</div>
            <div className="text-sm text-neutral-600">Per transaction</div>
          </div>
        </div>


        <div className="bg-white rounded-xl p-8 border border-neutral-200 mb-8">
          <h2 className="text-lg font-bold text-neutral-900 mb-6">Revenue Over Time</h2>

          <div className="relative h-80">

            <div className="absolute left-0 top-0 bottom-8 w-16 flex flex-col justify-between text-right pr-4 text-sm text-neutral-600 tabular-nums lining-nums">
              <div>{formatCurrency(maxValue)}</div>
              <div>{formatCurrency(maxValue * 0.75)}</div>
              <div>{formatCurrency(maxValue * 0.5)}</div>
              <div>{formatCurrency(maxValue * 0.25)}</div>
              <div>{formatCurrency(0)}</div>
            </div>


            <div className="ml-16 relative h-full">

              <div className="absolute inset-0 flex flex-col justify-between pb-8">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="border-t border-neutral-100" />
                ))}
              </div>

              {/* --- FIX #2: Added missing flex container --- */}
              <div className="absolute inset-0 flex gap-2 pb-8">
                {chartData.slice(0, timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : 90).map((data, i) => (
                  <div key={i} className="flex-1 flex flex-col items-center gap-3 group">
                    {/* --- FIX #3: Added flex-1 to this wrapper --- */}
                    <div className="relative w-full flex-1 flex flex-col-reverse items-center">

                      <div className="absolute -top-24 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity bg-neutral-900 text-white px-4 py-3 rounded-lg text-xs whitespace-nowrap pointer-events-none z-20 shadow-xl">
                        <div className="font-bold mb-1 tabular-nums lining-nums">{formatCurrency(data.revenue)}</div>
                        <div className="text-neutral-300 tabular-nums lining-nums">{data.transactions} tx</div>
                        <div className="text-neutral-400 tabular-nums lining-nums">{data.refunds} refunds</div>
                        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-full">
                          <div className="w-2 h-2 bg-neutral-900 rotate-45" />
                        </div>
                      </div>


                      <div
                        className="w-full rounded-t-lg transition-all duration-300 cursor-pointer relative overflow-hidden group-hover:scale-105"
                        style={{
                          height: `${((data.revenue || 0) / maxValue) * 100}%`,
                          minHeight: '8px',
                          background: 'linear-gradient(to top, #10b981, #34d399)'
                        }}
                      >
                        <div className="absolute inset-0 bg-gradient-to-t from-transparent via-white/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                      </div>
                    </div>
                    {timeRange === '7d' && (
                      <span className="text-xs font-medium text-neutral-600 group-hover:text-neutral-900">
                        {data.label}
                      </span>
                    )}
                  </div>
                ))}
                {chartData.length === 0 && (
                  <div className="absolute inset-0 flex items-center justify-center text-sm text-neutral-500">
                    No data
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {allZero && (
          <div className="bg-white rounded-xl p-6 border border-neutral-200 mb-8 text-center text-sm text-neutral-600">
            No revenue yet for this period. Create charges to see charts populate.
          </div>
        )}


        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-white rounded-xl p-8 border border-neutral-200">
            <h2 className="text-lg font-bold text-neutral-900 mb-6">Transaction Volume</h2>
            <div className="space-y-4">
              {chartData.slice(0, 7).map((data, i) => (
                <div key={i}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-neutral-700">{data.label}</span>
                    <span className="text-sm font-bold text-neutral-900 tabular-nums lining-nums">{data.transactions}</span>
                  </div>
                  <div className="w-full bg-neutral-100 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-blue-500 to-blue-600 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${Math.min(100, Math.round(((data.transactions || 0) / (Math.max(...chartData.map(d => d.transactions || 0), 1))) * 100))}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-xl p-8 border border-neutral-200">
            <h2 className="text-lg font-bold text-neutral-900 mb-6">Payment Methods</h2>
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-neutral-700">Credit Card</span>
                  <span className="text-sm font-bold text-neutral-900 tabular-nums lining-nums">65%</span>
                </div>
                <div className="w-full bg-neutral-100 rounded-full h-2">
                  <div className="bg-gradient-to-r from-emerald-500 to-emerald-600 h-2 rounded-full" style={{ width: '65%' }} />
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-neutral-700">Bank Transfer</span>
                  <span className="text-sm font-bold text-neutral-900 tabular-nums lining-nums">25%</span>
                </div>
                <div className="w-full bg-neutral-100 rounded-full h-2">
                  <div className="bg-gradient-to-r from-blue-500 to-blue-600 h-2 rounded-full" style={{ width: '25%' }} />
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-neutral-700">Wallet</span>
                  <span className="text-sm font-bold text-neutral-900 tabular-nums lining-nums">10%</span>
                </div>
                <div className="w-full bg-neutral-100 rounded-full h-2">
                  <div className="bg-gradient-to-r from-purple-500 to-purple-600 h-2 rounded-full" style={{ width: '10%' }} />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
