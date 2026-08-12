import { useEffect, useState } from 'react'
import apiClient from '../api/client'
import ErrorBanner from './ErrorBanner'
import { STATUS } from '../theme/palette'

// Mock connect flow: the owner pastes the access token a real OAuth
// redirect would eventually hand back (see backend routes/credentials.py).
// Swapping in real Meta OAuth later only touches this component.
const PROVIDERS = [{ key: 'instagram', label: 'Instagram' }]

function ConnectedAccounts({ businessId }) {
  const [connections, setConnections] = useState({})
  const [tokenInputs, setTokenInputs] = useState({})
  const [error, setError] = useState(null)
  const [busyProvider, setBusyProvider] = useState(null)

  const refresh = () => {
    apiClient
      .get(`/api/businesses/${businessId}/credentials`)
      .then((res) => {
        const byProvider = Object.fromEntries(res.data.map((c) => [c.provider, c]))
        setConnections(byProvider)
      })
      .catch(() => {})
  }

  useEffect(refresh, [businessId])

  const connect = async (provider) => {
    const accessToken = tokenInputs[provider]
    if (!accessToken) return
    setBusyProvider(provider)
    setError(null)
    try {
      await apiClient.post(`/api/businesses/${businessId}/credentials/${provider}/connect`, {
        access_token: accessToken,
        scopes: [],
      })
      setTokenInputs((prev) => ({ ...prev, [provider]: '' }))
      refresh()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to connect account')
    } finally {
      setBusyProvider(null)
    }
  }

  const disconnect = async (provider) => {
    setBusyProvider(provider)
    setError(null)
    try {
      await apiClient.delete(`/api/businesses/${businessId}/credentials/${provider}`)
      refresh()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to disconnect account')
    } finally {
      setBusyProvider(null)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-sm font-semibold text-gray-900 mb-1">Connected Accounts</h3>
      <p className="text-xs text-gray-400 mb-3">
        Agents only ever see "posted" or "failed" — the token itself never reaches an agent or
        leaves the server once connected.
      </p>
      <div className="space-y-3">
        {PROVIDERS.map(({ key, label }) => {
          const connection = connections[key]
          return (
            <div key={key} className="border rounded p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-800">{label}</span>
                {connection ? (
                  <span className="text-xs font-medium" style={{ color: STATUS.good }}>
                    connected
                  </span>
                ) : (
                  <span className="text-xs text-gray-400">not connected</span>
                )}
              </div>
              {connection ? (
                <button
                  type="button"
                  disabled={busyProvider === key}
                  onClick={() => disconnect(key)}
                  className="px-3 py-1 rounded text-white text-xs font-medium disabled:opacity-50"
                  style={{ backgroundColor: STATUS.critical }}
                >
                  Disconnect
                </button>
              ) : (
                <div className="flex gap-2">
                  <input
                    value={tokenInputs[key] || ''}
                    onChange={(e) => setTokenInputs((prev) => ({ ...prev, [key]: e.target.value }))}
                    placeholder="Paste access token"
                    className="flex-1 border rounded px-2 py-1 text-xs"
                  />
                  <button
                    type="button"
                    disabled={busyProvider === key}
                    onClick={() => connect(key)}
                    className="px-3 py-1 rounded text-white text-xs font-medium disabled:opacity-50"
                    style={{ backgroundColor: STATUS.good }}
                  >
                    Connect
                  </button>
                </div>
              )}
            </div>
          )
        })}
      </div>
      {error && <div className="mt-2"><ErrorBanner message={error} /></div>}
    </div>
  )
}

export default ConnectedAccounts
