import { useState } from 'react'
import apiClient from '../api/client'
import useVisiblePolling from '../hooks/useVisiblePolling'

export default function CEOSupervision({ businessId }) {
  const [goal, setGoal] = useState('')
  const [plans, setPlans] = useState([])
  const [reports, setReports] = useState([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  async function load() {
    try {
      const [p, r] = await Promise.all([
        apiClient.get(`/api/businesses/${businessId}/ceo/plans`),
        apiClient.get(`/api/businesses/${businessId}/ceo/reports`),
      ])
      setPlans(p.data); setReports(r.data)
    } catch { setError('Could not load CEO plans and department reports.') }
  }
  useVisiblePolling(load, 5000, [businessId])
  async function run(action) {
    setBusy(true); setError('')
    try { await action(); await load() }
    catch (e) { setError(typeof e.response?.data?.detail === 'string' ? e.response.data.detail : 'The request failed. Please try again.') }
    finally { setBusy(false) }
  }
  return <section className="bg-white rounded-lg shadow p-4 space-y-4">
    <h2 className="font-semibold">CEO plans and department reports</h2>
    <p className="text-sm text-gray-600">Set a goal. The CEO proposes assignments for Finance, Marketing, HR, and Operations. Assigning a plan follows each department’s approval settings.</p>
    <form className="space-y-2" onSubmit={(e) => { e.preventDefault(); run(() => apiClient.post(`/api/businesses/${businessId}/ceo/plans`, { goal })) }}>
      <label htmlFor="ceo-goal" className="block text-sm">Business goal</label>
      <textarea id="ceo-goal" required minLength={5} maxLength={2000} value={goal} onChange={(e) => setGoal(e.target.value)} className="w-full border rounded p-2" placeholder="Grow customers while protecting our available budget" />
      <button disabled={busy} className="bg-gray-900 text-white rounded px-3 py-2 disabled:opacity-50">{busy ? 'Working…' : 'Ask CEO to plan'}</button>
    </form>
    {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
    <div className="space-y-3">
      {plans.length === 0 && <p className="text-sm text-gray-500">No plans yet.</p>}
      {plans.slice(0, 10).map((plan) => <article key={plan.plan_id} className="border rounded p-3 space-y-2">
        <h3 className="font-medium">{plan.goal}</h3>
        <p className="text-xs text-gray-500">{plan.status.replace(/_/g, ' ')}</p>
        <p className="text-sm">{plan.strategy}</p>
        <ul className="list-disc pl-5 text-sm space-y-2">{plan.assignments.map((a, i) => <li key={i}>
          <strong className="capitalize">{a.department}:</strong> {a.objective}
          <p className="text-gray-600">Target: {a.success_criteria}</p>
          <p className="text-xs text-gray-500">{a.action_type.replace(/_/g, ' ')} · {Object.entries(a.payload).map(([k, v]) => `${k}: ${v}`).join(' · ')}</p>
        </li>)}</ul>
        {plan.status === 'draft' && <button disabled={busy} onClick={() => run(() => apiClient.post(`/api/businesses/${businessId}/ceo/plans/${plan.plan_id}/activate`))} className="border rounded px-3 py-1 disabled:opacity-50">Assign plan to departments</button>}
      </article>)}
    </div>
    <h3 className="font-semibold">Reports to the CEO</h3>
    {reports.length === 0 && <p className="text-sm text-gray-500">Reports appear after departments execute their assignments.</p>}
    {reports.slice(0, 20).map((report) => <article key={report.report_id} className="border rounded p-3 text-sm space-y-1">
      <p><strong className="capitalize">{report.department}</strong> → CEO · {report.status}</p>
      <p>{report.objective}</p>
      {report.result && <p className="text-gray-600">{report.result.reasoning || report.result.reason || report.result.status}</p>}
      {!report.ceo_review && <p className="text-gray-500">CEO review pending; execution evidence has been saved.</p>}
      {report.ceo_review && <><p>CEO review: {report.ceo_review.assessment}</p><p className="text-gray-600">Next: {report.ceo_review.recommendation}</p></>}
    </article>)}
  </section>
}
