import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import apiClient from '../api/client'

function StatCard({ label, value }) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <p className="text-xs text-gray-500 uppercase mb-1">{label}</p>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
    </div>
  )
}

function AdminOverview() {
  const [businesses, setBusinesses] = useState([])
  const [health, setHealth] = useState(null)

  useEffect(() => {
    apiClient.get('/api/admin/businesses').then((res) => setBusinesses(res.data)).catch(() => {})
    apiClient.get('/api/admin/system-health').then((res) => setHealth(res.data)).catch(() => {})
  }, [])

  const recent = [...businesses]
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    .slice(0, 5)

  return (
    <div className="max-w-5xl mx-auto px-4 py-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Admin Overview</h1>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard label="Total businesses" value={businesses.length} />
        <StatCard label="Active simulations" value={health?.running_simulation_count ?? '—'} />
        <StatCard label="Registered users" value={health?.user_count ?? '—'} />
      </div>

      <div className="bg-white rounded-lg shadow p-4">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">Recently created businesses</h3>
        {recent.length === 0 ? (
          <p className="text-sm text-gray-400">No businesses yet.</p>
        ) : (
          <div className="space-y-1">
            {recent.map((b) => (
              <Link
                key={b.id}
                to={`/admin/businesses/${b.id}`}
                className="flex items-center justify-between text-sm px-2 py-1.5 rounded hover:bg-gray-50"
              >
                <span className="font-medium text-gray-900">{b.company_name}</span>
                <span className="text-gray-400">{b.owner_email}</span>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default AdminOverview
