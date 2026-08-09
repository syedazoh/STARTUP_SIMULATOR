import { useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import {
  pauseSimulation,
  resumeSimulation,
  startSimulation,
  stopSimulation,
} from '../store/slices/simulationSlice'
import ErrorBanner from './ErrorBanner'
import { STATUS } from '../theme/palette'

function SimulationControls({ businessId }) {
  const dispatch = useDispatch()
  const { isRunning, isPaused, tickCount, decisionLogSize, runId, error } = useSelector(
    (state) => state.simulation,
  )
  const [ticks, setTicks] = useState(20)
  const [durationSeconds, setDurationSeconds] = useState('')
  const [minInterval, setMinInterval] = useState(0.5)
  const [maxInterval, setMaxInterval] = useState(2)

  const handleStart = () => {
    dispatch(
      startSimulation({
        businessId,
        ticks: ticks === '' ? null : Number(ticks),
        durationSeconds: durationSeconds === '' ? null : Number(durationSeconds),
        minInterval: Number(minInterval),
        maxInterval: Number(maxInterval),
      }),
    )
  }

  const handleStop = () => dispatch(stopSimulation(businessId))
  const handlePause = () => dispatch(pauseSimulation(businessId))
  const handleResume = () => dispatch(resumeSimulation(businessId))

  const statusLabel = !isRunning ? 'Idle' : isPaused ? 'Paused' : 'Running'
  const statusColor = !isRunning ? undefined : isPaused ? STATUS.warning : STATUS.good

  return (
    <div className="bg-white rounded-lg shadow p-4 flex flex-wrap items-end gap-4">
      <div>
        <label className="block text-xs text-gray-500 mb-1" htmlFor="ticks">Ticks</label>
        <input
          id="ticks"
          type="number"
          min="1"
          value={ticks}
          onChange={(e) => setTicks(e.target.value)}
          disabled={isRunning}
          placeholder="unlimited"
          className="border rounded px-2 py-1 w-24 text-sm disabled:bg-gray-100"
        />
      </div>
      <div>
        <label className="block text-xs text-gray-500 mb-1" htmlFor="duration">Duration (s)</label>
        <input
          id="duration"
          type="number"
          min="0"
          value={durationSeconds}
          onChange={(e) => setDurationSeconds(e.target.value)}
          disabled={isRunning}
          placeholder="unlimited"
          className="border rounded px-2 py-1 w-24 text-sm disabled:bg-gray-100"
        />
      </div>
      <div>
        <label className="block text-xs text-gray-500 mb-1" htmlFor="min-interval">Min interval (s)</label>
        <input
          id="min-interval"
          type="number"
          min="0"
          step="0.1"
          value={minInterval}
          onChange={(e) => setMinInterval(e.target.value)}
          disabled={isRunning}
          className="border rounded px-2 py-1 w-24 text-sm disabled:bg-gray-100"
        />
      </div>
      <div>
        <label className="block text-xs text-gray-500 mb-1" htmlFor="max-interval">Max interval (s)</label>
        <input
          id="max-interval"
          type="number"
          min="0"
          step="0.1"
          value={maxInterval}
          onChange={(e) => setMaxInterval(e.target.value)}
          disabled={isRunning}
          className="border rounded px-2 py-1 w-24 text-sm disabled:bg-gray-100"
        />
      </div>

      <button
        type="button"
        onClick={handleStart}
        disabled={isRunning}
        className="px-4 py-2 rounded text-white text-sm font-medium disabled:opacity-50"
        style={{ backgroundColor: STATUS.good }}
      >
        Start
      </button>
      {!isPaused ? (
        <button
          type="button"
          onClick={handlePause}
          disabled={!isRunning}
          className="px-4 py-2 rounded text-white text-sm font-medium disabled:opacity-50"
          style={{ backgroundColor: STATUS.warning }}
        >
          Pause
        </button>
      ) : (
        <button
          type="button"
          onClick={handleResume}
          disabled={!isRunning}
          className="px-4 py-2 rounded text-white text-sm font-medium disabled:opacity-50"
          style={{ backgroundColor: STATUS.good }}
        >
          Resume
        </button>
      )}
      <button
        type="button"
        onClick={handleStop}
        disabled={!isRunning}
        className="px-4 py-2 rounded text-white text-sm font-medium disabled:opacity-50"
        style={{ backgroundColor: STATUS.critical }}
      >
        Stop
      </button>

      <div className="text-sm text-gray-600 ml-auto">
        <span className="mr-4">
          Status: <span className="font-medium" style={{ color: statusColor }}>{statusLabel}</span>
        </span>
        <span className="mr-4">Ticks: {tickCount}</span>
        <span className="mr-4">Decisions: {decisionLogSize}</span>
        {runId && <span className="text-xs text-gray-400">run: {runId.slice(0, 8)}</span>}
      </div>
      {error && <div className="w-full"><ErrorBanner message={error} /></div>}
    </div>
  )
}

export default SimulationControls
