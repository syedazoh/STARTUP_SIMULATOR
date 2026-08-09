import { useEffect, useState } from 'react'
import apiClient from '../api/client'
import { STATUS } from '../theme/palette'

function AgentPolicyForm({ businessId, agentKey, config }) {
  const [policy, setPolicy] = useState({ enabled: false, auto_approve_max: '', auto_deny_min: '' })
  const [status, setStatus] = useState('idle')

  useEffect(() => {
    apiClient.get(`/api/businesses/${businessId}/agents/${agentKey}/policy`).then((res) => {
      setPolicy({
        enabled: res.data.enabled,
        auto_approve_max: res.data.auto_approve_max ?? '',
        auto_deny_min: res.data.auto_deny_min ?? '',
      })
    })
  }, [businessId, agentKey])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setStatus('saving')
    await apiClient.put(`/api/businesses/${businessId}/agents/${agentKey}/policy`, {
      enabled: policy.enabled,
      auto_approve_max: policy.auto_approve_max === '' ? null : Number(policy.auto_approve_max),
      auto_deny_min: policy.auto_deny_min === '' ? null : Number(policy.auto_deny_min),
    })
    setStatus('saved')
    setTimeout(() => setStatus('idle'), 1500)
  }

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-sm font-semibold text-gray-900 mb-3">Automation Policy</h3>
      <form onSubmit={handleSubmit} className="space-y-3">
        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input
            type="checkbox"
            checked={policy.enabled}
            onChange={(e) => setPolicy((p) => ({ ...p, enabled: e.target.checked }))}
          />
          Enable automation
        </label>
        <div>
          <label className="block text-xs text-gray-500 mb-1">{config.policyLabels.auto_approve_max}</label>
          <input
            type="number"
            value={policy.auto_approve_max}
            onChange={(e) => setPolicy((p) => ({ ...p, auto_approve_max: e.target.value }))}
            placeholder="no limit"
            className="w-full border rounded px-2 py-1 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">{config.policyLabels.auto_deny_min}</label>
          <input
            type="number"
            value={policy.auto_deny_min}
            onChange={(e) => setPolicy((p) => ({ ...p, auto_deny_min: e.target.value }))}
            placeholder="no limit"
            className="w-full border rounded px-2 py-1 text-sm"
          />
        </div>
        <button
          type="submit"
          disabled={status === 'saving'}
          className="px-4 py-2 rounded text-white text-sm font-medium disabled:opacity-50"
          style={{ backgroundColor: STATUS.good }}
        >
          {status === 'saving' ? 'Saving…' : status === 'saved' ? 'Saved ✓' : 'Save Policy'}
        </button>
      </form>
    </div>
  )
}

export default AgentPolicyForm
