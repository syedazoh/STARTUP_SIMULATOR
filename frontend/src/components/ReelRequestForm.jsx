import { useState } from 'react'
import apiClient from '../api/client'
import ErrorBanner from './ErrorBanner'
import { STATUS } from '../theme/palette'

function ReelRequestForm({ businessId, onActionComplete }) {
  const [campaignName, setCampaignName] = useState('')
  const [brief, setBrief] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const response = await apiClient.post(
        `/api/businesses/${businessId}/agents/marketing/actions/reel-request`,
        { campaign_name: campaignName, brief },
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
      <h3 className="text-sm font-semibold text-gray-900 mb-1">Request a Reel</h3>
      <p className="text-xs text-gray-400 mb-3">
        Marketing will ask you to upload a video or image before this can be posted — check the
        Task Queue on the dashboard once submitted.
      </p>
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label className="block text-xs text-gray-500 mb-1">Campaign name</label>
          <input
            required
            value={campaignName}
            onChange={(e) => setCampaignName(e.target.value)}
            className="w-full border rounded px-2 py-1 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Brief</label>
          <textarea
            value={brief}
            onChange={(e) => setBrief(e.target.value)}
            rows={2}
            placeholder="e.g. upbeat, 15s, product in hand"
            className="w-full border rounded px-2 py-1 text-sm"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 rounded text-white text-sm font-medium disabled:opacity-50"
          style={{ backgroundColor: STATUS.good }}
        >
          {loading ? 'Submitting…' : 'Request Reel'}
        </button>
      </form>

      {error && <div className="mt-2"><ErrorBanner message={error} /></div>}

      {result && (
        <div className="mt-3 border-t pt-3 text-sm">
          <span className="font-medium text-gray-500">Status: </span>
          <span className="font-medium" style={{ color: STATUS.warning }}>
            {result.status.replace(/_/g, ' ')}
          </span>
        </div>
      )}
    </div>
  )
}

export default ReelRequestForm
