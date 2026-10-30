import { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Navigate, Outlet } from 'react-router-dom'
import { fetchMe, restoreSession } from '../store/slices/authSlice'

function ProtectedRoute() {
  const dispatch = useDispatch()
  const token = useSelector((state) => state.auth.token)
  const user = useSelector((state) => state.auth.user)
  const { initialized, status } = useSelector((state) => state.auth)

  useEffect(() => {
    if (token && !user) {
      dispatch(fetchMe())
    }
  }, [token, user, dispatch])

  useEffect(() => {
    if (!initialized && status !== 'loading') dispatch(restoreSession())
  }, [initialized, status, dispatch])

  if (!initialized) return <p className="p-6">Restoring your session…</p>
  if (!token) {
    return <Navigate to="/login" replace />
  }
  return <Outlet />
}

export default ProtectedRoute
