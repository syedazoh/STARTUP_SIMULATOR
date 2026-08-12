import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { approveTask, fetchPendingTasks, rejectTask, requestTaskChanges } from '../store/slices/tasksSlice'
import { STATUS } from '../theme/palette'

const POLL_INTERVAL_MS = 3000

function formatPayload(payload) {
  return Object.entries(payload)
    .map(([key, value]) => `${key}: ${value}`)
    .join(' · ')
}

function TaskCard({ task }) {
  const dispatch = useDispatch()
  const [feedback, setFeedback] = useState('')
  const [busy, setBusy] = useState(false)

  const run = async (thunk) => {
    setBusy(true)
    await dispatch(thunk)
    setBusy(false)
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
      </div>
      <p className="text-xs text-gray-500">{formatPayload(task.payload)}</p>
      {task.owner_feedback && (
        <p className="text-xs text-gray-400 italic">Your feedback: "{task.owner_feedback}"</p>
      )}

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
    </div>
  )
}

function TaskQueue({ businessId }) {
  const dispatch = useDispatch()
  const tasks = useSelector((state) => state.tasks.items)

  useEffect(() => {
    dispatch(fetchPendingTasks(businessId))
    const interval = setInterval(() => dispatch(fetchPendingTasks(businessId)), POLL_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [dispatch, businessId])

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
          {tasks.map((task) => (
            <TaskCard key={task.id} task={task} />
          ))}
        </div>
      )}
    </div>
  )
}

export default TaskQueue
