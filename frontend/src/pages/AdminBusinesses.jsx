import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import apiClient from '../api/client'
import { STATUS } from '../theme/palette'

const STATUS_COLOR = {
  running: STATUS.good,
  stopped: STATUS.warning,
  completed: STATUS.warning,
}

function AdminBusinesses() {
  const [businesses, setBusinesses] = useState([])

  useEffect(() => {
    apiClient.get('/api/admin/businesses').then((res) => setBusinesses(res.data)).catch(() => {})
  }, [])

  return (
    <div className="max-w-6xl mx-auto px-4 py-6 space-y-4">
      <h1 className="text-2xl font-bold text-gray-900">Businesses</h1>
      <div className="bg-white rounded-lg shadow overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-gray-500 uppercase border-b">
              <th className="px-4 py-2">Company</th>
              <th className="px-4 py-2">Owner</th>
              <th className="px-4 py-2">Industry</th>
              <th className="px-4 py-2">Simulation</th>
              <th className="px-4 py-2">Tasks</th>
              <th className="px-4 py-2">Created</th>
            </tr>
          </thead>
          <tbody>
            {businesses.map((b) => (
              <tr key={b.id} className="border-b last:border-0 hover:bg-gray-50">
                <td className="px-4 py-2">
                  <Link to={`/admin/businesses/${b.id}`} className="font-medium text-gray-900 hover:underline">
                    {b.company_name}
                  </Link>
                </td>
                <td className="px-4 py-2 text-gray-600">{b.owner_email}</td>
                <td className="px-4 py-2 text-gray-600">{b.industry}</td>
                <td className="px-4 py-2" style={{ color: STATUS_COLOR[b.simulation_status] || undefined }}>
                  {b.simulation_status.replace(/_/g, ' ')}
                </td>
                <td className="px-4 py-2 text-gray-600">
                  {b.task_count} ({b.pending_task_count} pending)
                </td>
                <td className="px-4 py-2 text-gray-400">{new Date(b.created_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {businesses.length === 0 && <p className="text-sm text-gray-400 p-4">No businesses yet.</p>}
      </div>
    </div>
  )
}

export default AdminBusinesses
