import { useState } from 'react'
import apiClient from '../api/client'
import ErrorBanner from './ErrorBanner'
import { STATUS } from '../theme/palette'

const GOOD_STATUSES = new Set(['posted', 'executed', 'auto_approved'])
const BAD_STATUSES = new Set(['failed', 'rejected'])
const WAITING_STATUSES = new Set(['pending_approval', 'needs_changes', 'awaiting_asset'])

function InstagramPostForm({ businessId, onActionComplete }) {
  const [content, setContent] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const response = await apiClient.post(
        `/api/businesses/${businessId}/agents/marketing/actions/instagram-post`,
        { content },
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
      <h3 className="text-sm font-semibold text-gray-900 mb-3">Post to Instagram</h3>
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label className="block text-xs text-gray-500 mb-1">Post content</label>
          <textarea
            required
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={3}
            className="w-full border rounded px-2 py-1 text-sm"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 rounded text-white text-sm font-medium disabled:opacity-50"
          style={{ backgroundColor: STATUS.good }}
        >
          {loading ? 'Submitting…' : 'Request Post'}
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
          {result.result?.reason && (
            <p className="text-gray-600">{result.result.reason.replace(/_/g, ' ')}</p>
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

export default InstagramPostForm
