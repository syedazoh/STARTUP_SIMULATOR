import { useEffect, useState } from 'react'
import apiClient from '../api/client'
import { STATUS } from '../theme/palette'

function AgentModeForm({ businessId, agentKey }) {
  const [mode, setMode] = useState({ mode: 'manual', autoApproveMax: '' })
  const [status, setStatus] = useState('idle')

  useEffect(() => {
    apiClient.get(`/api/businesses/${businessId}/agents/${agentKey}/mode`).then((res) => {
      setMode({
        mode: res.data.mode,
        autoApproveMax: res.data.auto_thresholds?.auto_approve_max ?? '',
      })
    })
  }, [businessId, agentKey])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setStatus('saving')
    await apiClient.put(`/api/businesses/${businessId}/agents/${agentKey}/mode`, {
      mode: mode.mode,
      auto_thresholds: {
        auto_approve_max: mode.autoApproveMax === '' ? null : Number(mode.autoApproveMax),
      },
    })
    setStatus('saved')
    setTimeout(() => setStatus('idle'), 1500)
  }

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-sm font-semibold text-gray-900 mb-1">Execution Mode</h3>
      <p className="text-xs text-gray-400 mb-3">
        Manual: every action from this agent waits in your task queue. Auto: actions within the
        threshold below execute immediately; everything else still waits for you.
      </p>
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="flex gap-4">
          {['manual', 'auto'].map((option) => (
            <label key={option} className="flex items-center gap-1 text-sm text-gray-700 capitalize">
              <input
                type="radio"
                name={`mode-${agentKey}`}
                checked={mode.mode === option}
                onChange={() => setMode((m) => ({ ...m, mode: option }))}
              />
              {option}
            </label>
          ))}
        </div>
        {mode.mode === 'auto' && (
          <div>
            <label className="block text-xs text-gray-500 mb-1">Auto-execute if under ($)</label>
            <input
              type="number"
              value={mode.autoApproveMax}
              onChange={(e) => setMode((m) => ({ ...m, autoApproveMax: e.target.value }))}
              placeholder="no limit — always waits for you"
              className="w-full border rounded px-2 py-1 text-sm"
            />
          </div>
        )}
        <button
          type="submit"
          disabled={status === 'saving'}
          className="px-4 py-2 rounded text-white text-sm font-medium disabled:opacity-50"
          style={{ backgroundColor: STATUS.good }}
        >
          {status === 'saving' ? 'Saving…' : status === 'saved' ? 'Saved ✓' : 'Save Mode'}
        </button>
      </form>
    </div>
  )
}

export default AgentModeForm
