import { useState } from 'react'
import apiClient from '../api/client'
import { useDispatch, useSelector } from 'react-redux'
import { approveTask, fetchPendingTasks, rejectTask, requestTaskChanges } from '../store/slices/tasksSlice'
import AssetUploadCard from './AssetUploadCard'
import useVisiblePolling from '../hooks/useVisiblePolling'
import { STATUS } from '../theme/palette'

const POLL_INTERVAL_MS = 3000
const INITIAL_VISIBLE_COUNT = 50
const LOAD_MORE_INCREMENT = 50

function formatPayload(payload) {
  return Object.entries(payload)
    .map(([key, value]) => `${key}: ${value}`)
    .join(' · ')
}

function TaskCard({ businessId, task }) {
  const dispatch = useDispatch()
  const [feedback, setFeedback] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const waitingCEO = ['pending_ceo_review', 'needs_revision', 'ceo_reviewing'].includes(task.status)

  const run = async (thunk) => {
    setBusy(true)
    setError('')
    try { await dispatch(thunk).unwrap() }
    catch { setError('Could not update the task. Refresh and retry.') }
    finally { setBusy(false) }
  }

  return (
    <div className="border rounded-lg p-3 space-y-2">
      <div className="flex items-center justify-between">
        <div>
          <span className="text-sm font-semibold text-gray-900 capitalize">{task.agent}</span>
          <span className="text-xs text-gray-400 ml-2">{task.action_type.replace(/_/g, ' ')}</span>
        </div>
        {task.status === 'needs_changes' && (
          <span className="text-xs font-medium" style={{ color: STATUS.warning }}>
            changes requested
          </span>
        )}
        {task.status === 'awaiting_asset' && (
          <span className="text-xs font-medium" style={{ color: STATUS.warning }}>
            needs an asset
          </span>
        )}
      </div>
      {task.objective && <p className="text-sm">{task.plan_id ? 'CEO assignment: ' : ''}{task.objective}</p>}
      {task.ceo_review && <p className="text-xs">CEO: {task.ceo_review.reason}</p>}
      {error && <p role="alert" className="text-red-700 text-sm">{error}</p>}
      <p className="text-xs text-gray-500">{formatPayload(task.payload)}</p>
      {task.owner_feedback && (
        <p className="text-xs text-gray-400 italic">Your feedback: "{task.owner_feedback}"</p>
      )}

      {task.status === 'awaiting_asset' ? (
        <AssetUploadCard businessId={businessId} task={task} />
      ) : waitingCEO ? (
        <button disabled={busy} onClick={async () => {
          setBusy(true); setError('')
          try { await apiClient.post(`/api/tasks/${task.id}/ceo-review`); await dispatch(fetchPendingTasks(businessId)).unwrap() }
          catch { setError('CEO review is unavailable. Open the department page to revise or retry.') }
          finally { setBusy(false) }
        }}>Retry CEO review · {task.status.replace(/_/g, ' ')}</button>
      ) : (
        <>
          <input
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Feedback (for reject / request changes)"
            className="w-full border rounded px-2 py-1 text-xs"
          />

          <div className="flex gap-2">
            <button
              type="button"
              disabled={busy}
              onClick={() => run(approveTask(task.id))}
              className="px-3 py-1 rounded text-white text-xs font-medium disabled:opacity-50"
              style={{ backgroundColor: STATUS.good }}
            >
              Approve
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={() => run(requestTaskChanges({ taskId: task.id, ownerFeedback: feedback }))}
              className="px-3 py-1 rounded text-white text-xs font-medium disabled:opacity-50"
              style={{ backgroundColor: STATUS.warning }}
            >
              Request changes
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={() => run(rejectTask({ taskId: task.id, ownerFeedback: feedback }))}
              className="px-3 py-1 rounded text-white text-xs font-medium disabled:opacity-50"
              style={{ backgroundColor: STATUS.critical }}
            >
              Reject
            </button>
          </div>
        </>
      )}
    </div>
  )
}

function TaskQueue({ businessId }) {
  const dispatch = useDispatch()
  const tasks = useSelector((state) => state.tasks.items)
  const [visibleCount, setVisibleCount] = useState(INITIAL_VISIBLE_COUNT)

  useVisiblePolling(() => dispatch(fetchPendingTasks(businessId)), POLL_INTERVAL_MS, [dispatch, businessId])

  const visibleTasks = tasks.slice(0, visibleCount)

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-900">Task Queue</h3>
        {tasks.length > 0 && (
          <span className="text-xs font-medium text-white rounded-full px-2 py-0.5" style={{ backgroundColor: STATUS.warning }}>
            {tasks.length} awaiting review
          </span>
        )}
      </div>
      {tasks.length === 0 ? (
        <p className="text-sm text-gray-400">Nothing waiting on you right now.</p>
      ) : (
        <div className="space-y-3">
          {visibleTasks.map((task) => (
            <TaskCard key={task.id} businessId={businessId} task={task} />
          ))}
          {visibleCount < tasks.length && (
            <button
              type="button"
              onClick={() => setVisibleCount((c) => c + LOAD_MORE_INCREMENT)}
              className="w-full text-xs font-medium text-gray-500 hover:text-gray-700 py-2"
            >
              Load more ({tasks.length - visibleCount} remaining)
            </button>
          )}
        </div>
      )}
    </div>
  )
}

export default TaskQueue
