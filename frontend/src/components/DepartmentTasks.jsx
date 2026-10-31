import { useState } from 'react'
import apiClient from '../api/client'
import useVisiblePolling from '../hooks/useVisiblePolling'
import AGENT_CONFIG from '../config/agentConfig'
import AssetUploadCard from './AssetUploadCard'

const editable = new Set(['pending_approval', 'needs_changes', 'pending_ceo_review', 'needs_revision'])
const label = (text) => text.replace(/_/g, ' ')

function Assignment({ task, businessId, refresh }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [editing, setEditing] = useState(false)
  const [proposal, setProposal] = useState(task.payload)
  const [objective, setObjective] = useState(task.objective || '')
  const run = async (action, body = {}) => {
    setBusy(true)
    setError('')
    try {
      await apiClient.post(`/api/tasks/${task.id}/${action}`, body)
      setEditing(false)
      await refresh()
    } catch (err) {
      setError(typeof err.response?.data?.detail === 'string' ? err.response.data.detail : 'Could not update this task. Please retry.')
    } finally { setBusy(false) }
  }
  return (
    <article className="border rounded p-3 space-y-2">
      <div className="flex justify-between gap-3 text-sm font-semibold">
        <span>{task.plan_id ? 'Assigned by CEO' : label(task.source)} · {label(task.agent)}</span>
        <span>{label(task.status)}</span>
      </div>
      <p>{task.objective || label(task.action_type)}</p>
      {task.success_criteria && <p className="text-sm">Success criteria: {task.success_criteria}</p>}
      <p className="text-xs text-gray-600">{Object.entries(task.payload).map(([k, v]) => `${label(k)}: ${v}`).join(' · ')}</p>
      {task.ceo_review && <p className="text-sm">CEO ({label(task.ceo_review.basis)}): {task.ceo_review.reason}</p>}
      {task.owner_feedback && <p className="text-sm">Owner feedback: {task.owner_feedback}</p>}
      {task.result && <p className="text-sm">Result: {task.result.reason || task.result.reasoning || task.result.status}{task.result.financial_amount !== undefined ? ` · Financial amount: $${task.result.financial_amount}` : ''}</p>}
      {task.status === 'awaiting_asset' && <AssetUploadCard businessId={businessId} task={task} />}
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
      <div className="flex flex-wrap gap-3 text-sm">
        {['pending_approval', 'needs_changes'].includes(task.status) && <button disabled={busy} onClick={() => run('approve')}>Approve execution</button>}
        {['pending_ceo_review', 'needs_revision', 'ceo_reviewing'].includes(task.status) && <button disabled={busy} onClick={() => run('ceo-review')}>Retry CEO review</button>}
        {editable.has(task.status) && <>
          <button disabled={busy} onClick={() => { setProposal(task.payload); setObjective(task.objective || ''); setEditing(!editing) }}>Revise proposal</button>
          <button disabled={busy} onClick={() => run('reject')}>Reject</button>
        </>}
        {task.action_type === 'budget_request' && task.status === 'executed' && <button disabled={busy} onClick={() => run('release-budget')}>Release unused allocation</button>}
      </div>
      {editing && <form className="space-y-2" onSubmit={(e) => { e.preventDefault(); run('revise', { payload: proposal, objective }) }}>
        <label className="block text-sm">Objective<input required className="block border rounded w-full p-1" value={objective} onChange={(e) => setObjective(e.target.value)} /></label>
        {Object.entries(proposal).map(([key, value]) => <label key={key} className="block text-sm">
          {AGENT_CONFIG[task.agent]?.actionFields.find((f) => f.name === key)?.label || label(key)}
          <input required className="block border rounded w-full p-1" type={typeof value === 'number' ? 'number' : 'text'} step="any" min={typeof value === 'number' ? 0 : undefined} value={value} onChange={(e) => setProposal({ ...proposal, [key]: typeof value === 'number' ? Number(e.target.value) : e.target.value })} />
        </label>)}
        <button disabled={busy} type="submit">Submit for new CEO authorization</button>
      </form>}
    </article>
  )
}

export default function DepartmentTasks({ businessId, agentKey }) {
  const [tasks, setTasks] = useState([])
  const [error, setError] = useState('')
  const [assignedOnly, setAssignedOnly] = useState(false)
  const refresh = async () => {
    try {
      const res = await apiClient.get(`/api/businesses/${businessId}/tasks`, { params: agentKey ? { agent: agentKey } : {} })
      setTasks(res.data)
      setError('')
    } catch { setError('Could not load tasks. Retrying automatically.') }
  }
  useVisiblePolling(refresh, 3000, [businessId, agentKey])
  const visible = tasks.filter((task) => !assignedOnly || task.plan_id)
  return <section className="bg-white rounded-lg shadow p-4 space-y-3">
    <h2 className="font-semibold">{agentKey ? 'Department tasks and CEO assignments' : 'All department assignments'}</h2>
    <p className="text-xs text-gray-500">Latest 200 tasks. Tasks stay visible after execution; department reports go to the CEO.</p>
    <label className="text-sm"><input type="checkbox" checked={assignedOnly} onChange={(e) => setAssignedOnly(e.target.checked)} /> Show CEO assignments only</label>
    {error && <p role="alert">{error}</p>}
    {!visible.length && <p className="text-sm text-gray-500">No tasks to show yet. Activate a CEO plan to assign work.</p>}
    {visible.map((task) => <Assignment key={task.id} task={task} businessId={businessId} refresh={refresh} />)}
  </section>
}
