import { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Navigate, Outlet } from 'react-router-dom'
import { fetchBusinesses } from '../store/slices/businessSlice'

function RequireBusiness() {
  const dispatch = useDispatch()
  const { items, status } = useSelector((state) => state.business)

  useEffect(() => {
    dispatch(fetchBusinesses())
  }, [dispatch])

  if (status === 'idle' || status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center text-sm text-gray-400">
        Loading…
      </div>
    )
  }

  if (status === 'failed') {
    return <section className="quick-start" aria-label="Business connection error">
      <h1>Your businesses could not load</h1>
      <p role="alert">This is a connection or account-access error, not confirmation that your businesses are missing. Check that the backend is running and uses your original MongoDB database.</p>
      <button type="button" onClick={() => dispatch(fetchBusinesses())}>Retry loading businesses</button>
      <p><a href="/login">Return to sign in</a></p>
    </section>
  }

  if (items.length === 0) {
    return <Navigate to="/onboarding" replace />
  }

  return <Outlet />
}

export default RequireBusiness
