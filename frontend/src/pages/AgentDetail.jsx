import '../studio/avatar.css';
import Recommendations from '../components/Recommendations'
import AgentAvatar from '../studio/AgentAvatar';
import { useState } from 'react'
import { useParams } from 'react-router-dom'
import apiClient from '../api/client'
import AGENT_CONFIG from '../config/agentConfig'
import AgentStatusCard from '../components/AgentStatusCard'
import AgentActionForm from '../components/AgentActionForm'
import AgentModeForm from '../components/AgentModeForm'
import AgentPolicyForm from '../components/AgentPolicyForm'
import AgentWorkflow from '../components/AgentWorkflow'
import CEOSupervision from '../components/CEOSupervision'
import DepartmentTasks from '../components/DepartmentTasks'
import FinancialSummary from '../components/FinancialSummary'
import AgentMetricChart from '../components/charts/AgentMetricChart'
import { CATEGORICAL } from '../theme/palette'
import { toChartData } from '../utils/chartData'
import useVisiblePolling from '../hooks/useVisiblePolling'

const loadThree=()=>import('three')
const POLL_INTERVAL_MS = 1500
const CHART_COLORS = [CATEGORICAL.blue, CATEGORICAL.orange, CATEGORICAL.aqua]

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
      .catch((err) => console.warn('Agent status could not load'))
    apiClient
      .get(`/api/businesses/${businessId}/agents/${agentKey}/history`, { params: { limit: 50 } })
      .then((res) => setHistory(res.data))
      .catch((err) => console.warn('Agent history could not load'))
    if (agentKey === 'ceo') {
      apiClient
        .get(`/api/businesses/${businessId}/events`, { params: { limit: 100 } })
        .then((res) => setArbitrationEvents(res.data.filter((e) => e.event_type.startsWith('arbitration'))))
        .catch((err) => console.warn('Arbitration events could not load'))
    }
  }

  useVisiblePolling(poll, POLL_INTERVAL_MS, [businessId, agentKey])

  return (
    <div className="agent-classic-workspace min-h-screen bg-gray-50">
      <main className="max-w-5xl mx-auto px-4 py-6 space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">
          {config ? config.label : 'CEO'} Agent
        </h1>
        <AgentAvatar agent={agentKey} loadThree={loadThree} caption={`${config?.label||'CEO'} avatar`}/>
          <AgentWorkflow businessId={businessId} role={agentKey}/>{agentKey!=="strategy"&&<details><summary>Earlier saved recommendation records</summary><Recommendations businessId={businessId} role={agentKey}/></details>}
        {agentKey === 'ceo' && <CEOSupervision key={businessId} businessId={businessId} />}
        <DepartmentTasks key={`${businessId}:${agentKey}`} businessId={businessId} agentKey={agentKey === 'ceo' ? undefined : agentKey} />
        {agentKey === 'finance' && <FinancialSummary key={businessId} businessId={businessId} />}
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

        {config && !config.readOnly ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <AgentActionForm businessId={businessId} config={config} onActionComplete={poll} />
            <AgentModeForm businessId={businessId} agentKey={agentKey} />
            <AgentPolicyForm businessId={businessId} agentKey={agentKey} config={config} />
            {agentKey==='marketing'&&<p>Instagram and Facebook work stays as reviewable drafts in Recommendations. No social account connection or publishing credential is needed.</p>}
          </div>
        ) : agentKey==='strategy' ? <p>Strategy provides read-only positioning and risk analysis. Submit shared launch briefs above; owner decisions remain in the boardroom.</p> : (
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="text-sm font-semibold text-gray-900 mb-2">Arbitration Activity</h3>
            <p className="text-xs text-gray-400 mb-3">
              Alongside department planning and report review, the CEO resolves Finance–Marketing budget disputes.
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
