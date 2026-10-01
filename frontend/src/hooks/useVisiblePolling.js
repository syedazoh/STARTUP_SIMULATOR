import { useEffect, useRef } from 'react'

/**
 * Polls `callback` on an interval, pausing while the tab is hidden and
 * immediately resuming (with an instant poll) when it becomes visible again.
 *
 * `deps` restarts the interval the same way a useEffect dependency array
 * would (e.g. when businessId changes) — the callback itself doesn't need to
 * be listed since the latest version is always called via a ref.
 */
export default function useVisiblePolling(callback, intervalMs, deps = []) {
  const callbackRef = useRef(callback)
  useEffect(() => {
    callbackRef.current = callback
  })

  useEffect(() => {
    let intervalId = null

    const start = () => {
      if (intervalId !== null) return
      callbackRef.current()
      intervalId = setInterval(() => callbackRef.current(), intervalMs)
    }
    const stop = () => {
      if (intervalId !== null) {
        clearInterval(intervalId)
        intervalId = null
      }
    }
    const handleVisibilityChange = () => {
      if (document.hidden) stop()
      else start()
    }

    if (!document.hidden) start()
    document.addEventListener('visibilitychange', handleVisibilityChange)

    return () => {
      stop()
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [intervalMs, ...deps])
}
