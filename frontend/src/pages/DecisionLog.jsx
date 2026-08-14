import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { useParams } from 'react-router-dom'
import apiClient from '../api/client'
import { STATUS } from '../theme/palette'

function formatTimestamp(ts) {
  return new Date(ts).toLocaleString()
}

function DecisionLog() {
  const { businessId } = useParams()
  const dispatch = useDispatch()
  const [entries, setEntries] = useState([])
  const [runs, setRuns] = useState([])
  const [selectedRunId, setSelectedRunId] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    apiClient.get(`/api/businesses/${businessId}/simulation-runs`)
      .then((res) => setRuns(res.data))
      .catch(() => {})
  }, [businessId])

  useEffect(() => {
    setLoading(true)
    setError(null)
    const url = `/api/businesses/${businessId}/simulation/decision-log${selectedRunId ? `?run_id=${selectedRunId}` : ''}`
    apiClient.get(url)
      .then((res) => {
        setEntries(res.data)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.response?.data?.detail || 'Failed to load decision log')
        setLoading(false)
      })
  }, [businessId, selectedRunId])

  const eventTypeColors = {
    budget_request: '#3B82F6',
    campaign_launch: '#8B5CF6',
    recruitment_request: '#10B981',
    resource_request: '#F59E0B',
    arbitration_request: '#EF4444',
    arbitration_result: '#EF4444',
    budget_negotiation: '#6366F1',
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2" style={{ borderColor: STATUS.good }} />
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6 text-center">
        <p className="text-red-500">{error}</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Decision Log</h3>
        {runs.length > 0 && (
          <select
            value={selectedRunId || ''}
            onChange={(e) => setSelectedRunId(e.target.value || null)}
            className="border rounded px-3 py-1 text-sm"
          >
            <option value="">All Runs</option>
            {runs.map((run) => (
              <option key={run.run_id} value={run.run_id}>
                {run.run_id.slice(0, 8)} — {formatTimestamp(run.started_at)} ({run.status})
              </option>
            ))}
          </select>
        )}
      </div>

      {entries.length === 0 ? (
        <p className="text-sm text-gray-400 text-center py-8">No decisions recorded yet.</p>
      ) : (
        <div className="space-y-3 max-h-[600px] overflow-y-auto">
          {entries.map((entry, i) => (
            <div key={i} className="border rounded-lg p-3 hover:bg-gray-50 transition-colors">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xs font-medium text-gray-500">Tick {entry.tick}</span>
                <span
                  className="px-2 py-0.5 rounded text-xs font-medium text-white"
                  style={{ backgroundColor: eventTypeColors[entry.event_type] || STATUS.good }}
                >
                  {entry.event_type.replace(/_/g, ' ')}
                </span>
                {entry.simulation_run_id && (
                  <span className="text-xs text-gray-400 ml-auto">{entry.simulation_run_id.slice(0, 8)}</span>
                )}
              </div>
              <p className="text-sm text-gray-700 font-mono">
                {JSON.stringify(entry.data, null, 2)}
              </p>
              <p className="text-xs text-gray-400 mt-1">
                Source: {entry.source} • {formatTimestamp(entry.timestamp)}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default DecisionLog