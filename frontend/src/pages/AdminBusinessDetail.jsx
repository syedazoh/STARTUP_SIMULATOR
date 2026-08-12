import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import apiClient from '../api/client'

function Field({ label, value }) {
  return (
    <div>
      <p className="text-xs text-gray-500">{label}</p>
      <p className="font-medium text-gray-900">{value}</p>
    </div>
  )
}

function AdminBusinessDetail() {
  const { businessId } = useParams()
  const [business, setBusiness] = useState(null)

  useEffect(() => {
    setBusiness(null)
    apiClient.get(`/api/admin/businesses/${businessId}`).then((res) => setBusiness(res.data)).catch(() => {})
  }, [businessId])

  if (!business) {
    return <div className="max-w-3xl mx-auto px-4 py-6 text-sm text-gray-400">Loading…</div>
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{business.company_name}</h1>
        <p className="text-xs text-gray-400 mt-1">
          No credential or secret data is ever shown here — the admin surface has no access to the
          credential vault by design.
        </p>
      </div>

      <div className="bg-white rounded-lg shadow p-4 grid grid-cols-2 gap-4 text-sm">
        <Field label="Owner" value={business.owner_email} />
        <Field label="Industry" value={business.industry} />
        <Field label="Simulation status" value={business.simulation_status.replace(/_/g, ' ')} />
        <Field label="Created" value={new Date(business.created_at).toLocaleString()} />
        <Field label="Starting budget" value={`$${business.starting_budget.toLocaleString()}`} />
        <Field label="Starting customers" value={business.starting_customer_base} />
        <Field label="Starting headcount" value={business.starting_headcount} />
        <Field label="Starting resources" value={business.starting_resources} />
      </div>

      <div className="bg-white rounded-lg shadow p-4">
        <h3 className="text-sm font-semibold text-gray-900 mb-2">Agent activity</h3>
        <p className="text-sm text-gray-600 mb-3">{business.decision_count} decisions logged</p>
        <div className="flex flex-wrap gap-2">
          {Object.entries(business.task_status_counts).map(([status, count]) => (
            <span key={status} className="text-xs bg-gray-100 rounded-full px-3 py-1">
              {status.replace(/_/g, ' ')}: {count}
            </span>
          ))}
          {Object.keys(business.task_status_counts).length === 0 && (
            <p className="text-sm text-gray-400">No tasks yet.</p>
          )}
        </div>
      </div>
    </div>
  )
}

export default AdminBusinessDetail
