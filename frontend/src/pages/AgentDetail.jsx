import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import apiClient from '../api/client'
import AGENT_CONFIG from '../config/agentConfig'
import AgentStatusCard from '../components/AgentStatusCard'
import AgentActionForm from '../components/AgentActionForm'
import AgentModeForm from '../components/AgentModeForm'
import AgentPolicyForm from '../components/AgentPolicyForm'
import AgentMetricChart from '../components/charts/AgentMetricChart'
import { CATEGORICAL } from '../theme/palette'

const POLL_INTERVAL_MS = 1500
const CHART_COLORS = [CATEGORICAL.blue, CATEGORICAL.orange, CATEGORICAL.aqua]

function toChartData(snapshots, metricKey) {
  return [...snapshots].reverse().map((snap, i) => ({
    tick: i + 1,
    [metricKey]: snap.state?.[metricKey],
  }))
}

function AgentDetail() {
  const { businessId, agentKey } = useParams()
  const config = AGENT_CONFIG[agentKey]
  const [status, setStatus] = useState(null)
  const [history, setHistory] = useState([])
  const [arbitrationEvents, setArbitrationEvents] = useState([])

  const poll = () => {
    apiClient
      .get(`/api/businesses/${businessId}/agents/${agentKey}`)
      .then((res) => setStatus(res.data))
      .catch(() => {})
    apiClient
      .get(`/api/businesses/${businessId}/agents/${agentKey}/history`, { params: { limit: 50 } })
      .then((res) => setHistory(res.data))
      .catch(() => {})
    if (agentKey === 'ceo') {
      apiClient
        .get(`/api/businesses/${businessId}/events`, { params: { limit: 100 } })
        .then((res) => setArbitrationEvents(res.data.filter((e) => e.event_type.startsWith('arbitration'))))
        .catch(() => {})
    }
  }

  useEffect(() => {
    poll()
    const interval = setInterval(poll, POLL_INTERVAL_MS)
    return () => clearInterval(interval)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [businessId, agentKey])

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-5xl mx-auto px-4 py-6 space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">
          {config ? config.label : 'CEO'} Agent
        </h1>
        {status && <AgentStatusCard agentKey={agentKey} status={status} />}

        {config && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {config.metricKeys.map((key, i) => (
              <AgentMetricChart
                key={key}
                title={key.replace(/_/g, ' ')}
                data={toChartData(history, key)}
                dataKey={key}
                color={CHART_COLORS[i % CHART_COLORS.length]}
              />
            ))}
          </div>
        )}

        {config ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <AgentActionForm businessId={businessId} config={config} onActionComplete={poll} />
            <AgentModeForm businessId={businessId} agentKey={agentKey} />
            <AgentPolicyForm businessId={businessId} agentKey={agentKey} config={config} />
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="text-sm font-semibold text-gray-900 mb-2">Arbitration Activity</h3>
            <p className="text-xs text-gray-400 mb-3">
              The CEO arbitrates automatically when Finance and Marketing disagree — there's no
              manual trigger or automation policy for this role.
            </p>
            {arbitrationEvents.length === 0 ? (
              <p className="text-sm text-gray-400">No arbitration events yet.</p>
            ) : (
              <div className="space-y-2">
                {arbitrationEvents.map((e) => (
                  <div
                    key={e.event_id}
                    className="border-l-2 pl-3 py-1"
                    style={{ borderColor: CATEGORICAL.magenta }}
                  >
                    <div className="text-sm font-medium text-gray-900">{e.event_type}</div>
                    <pre className="text-xs text-gray-600 whitespace-pre-wrap break-words">
                      {JSON.stringify(e.data)}
                    </pre>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}

export default AgentDetail
