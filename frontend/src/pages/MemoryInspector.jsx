import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import apiClient from '../api/client'
import { CATEGORICAL } from '../theme/palette'

const AGENTS = [
  { key: 'finance', label: 'Finance' },
  { key: 'marketing', label: 'Marketing' },
  { key: 'hr', label: 'HR' },
  { key: 'operations', label: 'Operations' },
  { key: 'ceo', label: 'CEO' },
]

function MemoryInspector() {
  const { businessId } = useParams()
  const [agentKey, setAgentKey] = useState('finance')
  const [query, setQuery] = useState('')
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(false)

  const search = (q) => {
    setLoading(true)
    apiClient
      .get(`/api/businesses/${businessId}/agents/${agentKey}/memory`, {
        params: q ? { query: q, k: 10 } : { k: 10 },
      })
      .then((res) => setEntries(res.data))
      .catch(() => setEntries([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    setQuery('')
    search('')
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [businessId, agentKey])

  const handleSubmit = (e) => {
    e.preventDefault()
    search(query)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Memory Inspector</h1>
          <p className="text-sm text-gray-500 mt-1">
            Vector search over each agent's past decisions — the same memory every agent draws on
            as precedent when it makes a new one.
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-4 space-y-4">
          <div className="flex gap-2">
            {AGENTS.map((a) => (
              <button
                key={a.key}
                type="button"
                onClick={() => setAgentKey(a.key)}
                className="px-3 py-1.5 rounded text-sm font-medium border"
                style={
                  agentKey === a.key
                    ? { backgroundColor: CATEGORICAL.blue, color: 'white', borderColor: CATEGORICAL.blue }
                    : { color: '#374151', borderColor: '#e5e7eb' }
                }
              >
                {a.label}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="flex gap-2">
            <label className="sr-only" htmlFor="memory-search">
              Search this agent's memory
            </label>
            <input
              id="memory-search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search this agent's memory (leave blank to browse recent entries)…"
              className="flex-1 border rounded px-3 py-2 text-sm"
            />
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 rounded text-white text-sm font-medium disabled:opacity-50"
              style={{ backgroundColor: CATEGORICAL.blue }}
            >
              {loading ? 'Searching…' : 'Search'}
            </button>
          </form>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="text-sm font-semibold text-gray-900 mb-3">
            {query ? `Results for "${query}"` : 'Recent memory'}
          </h3>
          {entries.length === 0 ? (
            <p className="text-sm text-gray-400">
              No memories yet — this agent hasn't made a decision that got recorded, or nothing
              matched your search.
            </p>
          ) : (
            <div className="space-y-3">
              {entries.map((entry, i) => (
                <div key={i} className="border-l-2 pl-3 py-1" style={{ borderColor: CATEGORICAL.aqua }}>
                  <p className="text-sm text-gray-800">{entry.document}</p>
                  <div className="flex items-center gap-3 mt-1">
                    {entry.distance !== null && entry.distance !== undefined && (
                      <span className="text-xs text-gray-400">distance: {entry.distance.toFixed(3)}</span>
                    )}
                    {Object.entries(entry.metadata || {})
                      .filter(([key]) => key !== 'agent_id' && key !== 'event_type')
                      .map(([key, value]) => (
                        <span key={key} className="text-xs text-gray-400">
                          {key}: {String(value)}
                        </span>
                      ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

export default MemoryInspector
