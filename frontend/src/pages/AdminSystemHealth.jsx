import { useState } from 'react'
import apiClient from '../api/client'
import useVisiblePolling from '../hooks/useVisiblePolling'
import { STATUS } from '../theme/palette'

const POLL_INTERVAL_MS = 5000

function HealthCard({ label, value, color }) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <p className="text-xs text-gray-500 uppercase mb-1">{label}</p>
      <p className="text-lg font-bold" style={{ color: color || '#111827' }}>
        {value}
      </p>
    </div>
  )
}

function AdminSystemHealth() {
  const [health, setHealth] = useState(null)

  useVisiblePolling(
    () => {
      apiClient.get('/api/admin/system-health').then((res) => setHealth(res.data)).catch(() => {})
    },
    POLL_INTERVAL_MS,
    [],
  )

  if (!health) {
    return <div className="max-w-3xl mx-auto px-4 py-6 text-sm text-gray-400">Loading…</div>
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">System Health</h1>
      <div className="grid grid-cols-2 gap-4">
        <HealthCard
          label="MongoDB"
          value={health.mongo_connected ? 'Connected' : 'Unavailable (in-memory fallback)'}
          color={health.mongo_connected ? STATUS.good : STATUS.critical}
        />
        <HealthCard label="Running simulations" value={health.running_simulation_count} />
        <HealthCard label="Total businesses" value={health.business_count} />
        <HealthCard label="Registered users" value={health.user_count} />
      </div>
    </div>
  )
}

export default AdminSystemHealth
