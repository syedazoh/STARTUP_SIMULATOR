import { useEffect, useRef, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Link, useParams } from 'react-router-dom'
import apiClient from '../api/client'
import { fetchAgents } from '../store/slices/agentsSlice'
import {
  clearSummary,
  fetchRunSummary,
  fetchSimulationStatus,
  resetSimulationState,
} from '../store/slices/simulationSlice'
import AgentStatusCard from '../components/AgentStatusCard'
import DecisionFeed from '../components/DecisionFeed'
import SimulationControls from '../components/SimulationControls'
import EndOfRunSummary from '../components/EndOfRunSummary'
import TaskQueue from '../components/TaskQueue'
import AgentMetricChart from '../components/charts/AgentMetricChart'
import { CATEGORICAL } from '../theme/palette'

const POLL_INTERVAL_MS = 1500

function toChartData(snapshots, metricKey) {
  // Snapshots arrive newest-first; reverse to chronological order for the x-axis.
  return [...snapshots].reverse().map((snap, i) => ({
    tick: i + 1,
    [metricKey]: snap.state?.[metricKey],
  }))
}

function Dashboard() {
  const { businessId } = useParams()
  const dispatch = useDispatch()
  const agentStatuses = useSelector((state) => state.agents.statuses)
  const { isRunning, runId, summary } = useSelector((state) => state.simulation)
  const [financeHistory, setFinanceHistory] = useState([])
  const [marketingHistory, setMarketingHistory] = useState([])
  const wasRunning = useRef(false)

  useEffect(() => {
    dispatch(resetSimulationState())
    wasRunning.current = false
  }, [businessId, dispatch])

  useEffect(() => {
    const poll = () => {
      dispatch(fetchAgents(businessId))
      dispatch(fetchSimulationStatus(businessId))
      apiClient
        .get(`/api/businesses/${businessId}/agents/finance/history`, { params: { limit: 50 } })
        .then((res) => setFinanceHistory(res.data))
        .catch(() => {})
      apiClient
        .get(`/api/businesses/${businessId}/agents/marketing/history`, { params: { limit: 50 } })
        .then((res) => setMarketingHistory(res.data))
        .catch(() => {})
    }
    poll()
    const interval = setInterval(poll, POLL_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [dispatch, businessId])

  useEffect(() => {
    if (wasRunning.current && !isRunning && runId) {
      dispatch(fetchRunSummary({ businessId, runId }))
    }
    wasRunning.current = isRunning
  }, [isRunning, runId, businessId, dispatch])

  useEffect(() => {
    if (isRunning) dispatch(clearSummary())
  }, [isRunning, dispatch])

  const agentEntries = Object.entries(agentStatuses)

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        <SimulationControls businessId={businessId} />

        {summary && <EndOfRunSummary summary={summary} />}

        <div>
          <h2 className="text-sm font-semibold text-gray-500 uppercase mb-2">Agents</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            {agentEntries.map(([key, status]) => (
              <Link key={key} to={`/b/${businessId}/agents/${key}`} className="block hover:opacity-80">
                <AgentStatusCard agentKey={key} status={status} />
              </Link>
            ))}
          </div>
        </div>

        <div>
          <h2 className="text-sm font-semibold text-gray-500 uppercase mb-2">Metrics</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <AgentMetricChart
              title="Finance: Budget Pool"
              data={toChartData(financeHistory, 'budget_pool')}
              dataKey="budget_pool"
              color={CATEGORICAL.blue}
              valueFormatter={(v) => `$${Math.round(v / 1000)}k`}
            />
            <AgentMetricChart
              title="Marketing: Customer Base"
              data={toChartData(marketingHistory, 'customer_base')}
              dataKey="customer_base"
              color={CATEGORICAL.orange}
            />
            <AgentMetricChart
              title="Marketing: Brand Value"
              data={toChartData(marketingHistory, 'brand_value')}
              dataKey="brand_value"
              color={CATEGORICAL.aqua}
              valueFormatter={(v) => v.toFixed(0)}
            />
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <TaskQueue businessId={businessId} />
          <DecisionFeed businessId={businessId} />
        </div>
      </main>
    </div>
  )
}

export default Dashboard
