import { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Navigate, Outlet } from 'react-router-dom'
import { fetchMe } from '../store/slices/authSlice'

function ProtectedRoute() {
  const dispatch = useDispatch()
  const token = useSelector((state) => state.auth.token)
  const user = useSelector((state) => state.auth.user)

  useEffect(() => {
    if (token && !user) {
      dispatch(fetchMe())
    }
  }, [token, user, dispatch])

  if (!token) {
    return <Navigate to="/login" replace />
  }
  return <Outlet />
}

export default ProtectedRoute
