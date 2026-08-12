import { useEffect, useRef, useState } from 'react'
import apiClient from '../api/client'
import ErrorBanner from './ErrorBanner'
import { STATUS } from '../theme/palette'

function ChatPanel({ businessId, agentKey, agentLabel }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState(null)
  const [lastTask, setLastTask] = useState(null)
  const scrollRef = useRef(null)

  useEffect(() => {
    setMessages([])
    setLastTask(null)
    apiClient
      .get(`/api/businesses/${businessId}/agents/${agentKey}/chat`)
      .then((res) => setMessages(res.data.messages))
      .catch(() => {})
  }, [businessId, agentKey])

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight })
  }, [messages])

  const handleSubmit = async (e) => {
    e.preventDefault()
    const content = input.trim()
    if (!content) return
    setSending(true)
    setError(null)
    setInput('')
    try {
      const response = await apiClient.post(`/api/businesses/${businessId}/agents/${agentKey}/chat`, {
        content,
      })
      setMessages(response.data.thread.messages)
      setLastTask(response.data.task)
    } catch (err) {
      setError(err.response?.data?.detail || 'Message failed to send')
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow p-4 flex flex-col h-full">
      <h3 className="text-sm font-semibold text-gray-900 mb-3">Chat with {agentLabel}</h3>

      <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-2 max-h-[360px] min-h-[160px] mb-3">
        {messages.length === 0 && (
          <p className="text-sm text-gray-400">No messages yet — ask {agentLabel} something.</p>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'owner' ? 'justify-end' : 'justify-start'}`}>
            <div
              className="max-w-[80%] rounded px-3 py-2 text-sm"
              style={
                msg.role === 'owner'
                  ? { backgroundColor: STATUS.good, color: 'white' }
                  : { backgroundColor: '#f3f4f6', color: '#111827' }
              }
            >
              {msg.content}
            </div>
          </div>
        ))}
      </div>

      {lastTask && (
        <p className="text-xs mb-2" style={{ color: STATUS.warning }}>
          Queued a "{lastTask.action_type.replace(/_/g, ' ')}" task ({lastTask.status.replace(/_/g, ' ')}) —
          check the Task Queue on the dashboard.
        </p>
      )}

      {error && <div className="mb-2"><ErrorBanner message={error} /></div>}

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={`Message ${agentLabel}…`}
          className="flex-1 border rounded px-2 py-1 text-sm"
        />
        <button
          type="submit"
          disabled={sending || !input.trim()}
          className="px-4 py-1 rounded text-white text-sm font-medium disabled:opacity-50"
          style={{ backgroundColor: STATUS.good }}
        >
          {sending ? 'Sending…' : 'Send'}
        </button>
      </form>
    </div>
  )
}

export default ChatPanel
