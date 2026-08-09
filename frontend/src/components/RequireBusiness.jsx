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

  if (items.length === 0) {
    return <Navigate to="/onboarding" replace />
  }

  return <Outlet />
}

export default RequireBusiness
