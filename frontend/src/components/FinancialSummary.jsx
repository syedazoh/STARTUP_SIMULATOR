import { useState } from 'react'
import apiClient from '../api/client'
import useVisiblePolling from '../hooks/useVisiblePolling'

export default function FinancialSummary({ businessId }) {
  const [account, setAccount] = useState(null)
  const [error, setError] = useState('')
  useVisiblePolling(async () => {
    try {
      const res = await apiClient.get(`/api/businesses/${businessId}/finances`)
      setAccount(res.data)
      setError('')
    } catch { setError('Could not load the financial ledger.') }
  }, 3000, [businessId])
  return <section className="bg-white rounded-lg shadow p-4 space-y-3">
    <h2 className="font-semibold">Shared financial ledger</h2>
    {error && <p role="alert">{error}</p>}
    {account && <dl className="grid grid-cols-2 gap-3 text-sm">{['cash', 'reserved', 'available', 'revenue', 'expenses', 'monthly_payroll_commitment'].map((key) => <div key={key}><dt className="capitalize">{key.replace(/_/g, ' ')}</dt><dd>${account[key].toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</dd></div>)}</dl>}
    <p className="text-xs text-gray-500">Allocations reserve cash. Actual work records expenses. Recruitment charges the first month and records a monthly commitment; recurring payroll is not yet scheduled.</p>
  </section>
}
