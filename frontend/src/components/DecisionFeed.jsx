import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { fetchEvents } from '../store/slices/eventsSlice'
import { CATEGORICAL } from '../theme/palette'

const POLL_INTERVAL_MS = 1500
const INITIAL_VISIBLE_COUNT = 50
const LOAD_MORE_INCREMENT = 50

// Fixed identity color per event type — never reassigned by rank/position in the feed.
const EVENT_COLORS = {
  campaign_launch: CATEGORICAL.blue,
  budget_request: CATEGORICAL.orange,
  budget_negotiation: CATEGORICAL.aqua,
  arbitration_request: CATEGORICAL.yellow,
  arbitration_result: CATEGORICAL.magenta,
  recruitment_request: CATEGORICAL.green,
  resource_request: CATEGORICAL.violet,
}
const DEFAULT_COLOR = CATEGORICAL.red

function formatTime(isoString) {
  try {
    return new Date(isoString).toLocaleTimeString()
  } catch {
    return isoString
  }
}

function DecisionFeed({ businessId }) {
  const dispatch = useDispatch()
  const events = useSelector((state) => state.events.items)
  const [visibleCount, setVisibleCount] = useState(INITIAL_VISIBLE_COUNT)
  const [prevBusinessId, setPrevBusinessId] = useState(businessId)
  if (businessId !== prevBusinessId) {
    setPrevBusinessId(businessId)
    setVisibleCount(INITIAL_VISIBLE_COUNT)
  }

  useEffect(() => {
    dispatch(fetchEvents(businessId))
    const interval = setInterval(() => dispatch(fetchEvents(businessId)), POLL_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [dispatch, businessId])

  const recent = [...events].reverse()
  const visible = recent.slice(0, visibleCount)

  return (
    <div className="bg-white rounded-lg shadow p-4 flex flex-col h-full">
      <h3 className="text-sm font-semibold text-gray-900 mb-3">Live Decision Feed</h3>
      <div className="flex-1 overflow-y-auto space-y-2 max-h-[420px]">
        {recent.length === 0 && (
          <p className="text-sm text-gray-400">No events yet.</p>
        )}
        {visible.map((event) => {
          const color = EVENT_COLORS[event.event_type] || DEFAULT_COLOR
          return (
            <div key={event.event_id} className="border-l-2 pl-3 py-1" style={{ borderColor: color }}>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-900">{event.event_type}</span>
                <span className="text-xs text-gray-400">{formatTime(event.timestamp)}</span>
              </div>
              <div className="text-xs text-gray-500">source: {event.source}</div>
              <pre className="text-xs text-gray-600 mt-1 whitespace-pre-wrap break-words">
                {JSON.stringify(event.data)}
              </pre>
            </div>
          )
        })}
        {visibleCount < recent.length && (
          <button
            type="button"
            onClick={() => setVisibleCount((c) => c + LOAD_MORE_INCREMENT)}
            className="w-full text-xs font-medium text-gray-500 hover:text-gray-700 py-2"
          >
            Load more ({recent.length - visibleCount} remaining)
          </button>
        )}
      </div>
    </div>
  )
}

export default DecisionFeed
