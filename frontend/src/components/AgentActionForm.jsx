import { useState } from 'react'
import apiClient from '../api/client'
import ErrorBanner from './ErrorBanner'
import { STATUS } from '../theme/palette'

// Finance's action endpoint returns a Task ({status: "pending_approval" |
// "auto_approved" | "executed" | "failed", result: {...} | null}); the other
// three agents still return the agent's raw decision ({status: "approved" |
// "denied", reasoning}) directly. Handling both shapes here means this form
// doesn't need to know which agent it's talking to.
const GOOD_STATUSES = new Set(['approved', 'executed', 'auto_approved'])
const BAD_STATUSES = new Set(['denied', 'rejected', 'failed'])
const WAITING_STATUSES = new Set(['pending_approval', 'needs_changes', 'awaiting_asset'])

function AgentActionForm({ businessId, config, onActionComplete }) {
  const [values, setValues] = useState(
    Object.fromEntries(config.actionFields.map((f) => [f.name, f.default])),
  )
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const update = (field) => (e) => {
    const raw = e.target.value
    setValues((prev) => ({ ...prev, [field.name]: field.type === 'number' ? Number(raw) : raw }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const response = await apiClient.post(
        `/api/businesses/${businessId}/agents/${config.actionEndpoint}`,
        values,
      )
      setResult(response.data)
      onActionComplete?.()
    } catch (err) {
      setError(err.response?.data?.detail || 'Action failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-sm font-semibold text-gray-900 mb-3">Manual Action</h3>
      <form onSubmit={handleSubmit} className="space-y-3">
        {config.actionFields.map((field) => (
          <div key={field.name}>
            <label className="block text-xs text-gray-500 mb-1" htmlFor={`action-${field.name}`}>
              {field.label}
            </label>
            <input
              id={`action-${field.name}`}
              type={field.type}
              value={values[field.name]}
              onChange={update(field)}
              className="w-full border rounded px-2 py-1 text-sm"
            />
          </div>
        ))}
        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 rounded text-white text-sm font-medium disabled:opacity-50"
          style={{ backgroundColor: STATUS.good }}
        >
          {loading ? 'Submitting…' : 'Trigger Action'}
        </button>
      </form>

      {error && <div className="mt-2"><ErrorBanner message={error} /></div>}

      {result && (
        <div className="mt-3 border-t pt-3 text-sm">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-medium text-gray-500">Result:</span>
            <span
              className="font-medium"
              style={{
                color: GOOD_STATUSES.has(result.status)
                  ? STATUS.good
                  : BAD_STATUSES.has(result.status)
                    ? STATUS.critical
                    : STATUS.warning,
              }}
            >
              {result.status.replace(/_/g, ' ')}
            </span>
          </div>
          {(result.reasoning || result.result?.reasoning) && (
            <p className="text-gray-600">{result.reasoning || result.result.reasoning}</p>
          )}
          {WAITING_STATUSES.has(result.status) && (
            <p className="text-xs text-gray-400 mt-1">
              Queued for your review — see the Task Queue on the dashboard.
            </p>
          )}
        </div>
      )}
    </div>
  )
}

export default AgentActionForm
