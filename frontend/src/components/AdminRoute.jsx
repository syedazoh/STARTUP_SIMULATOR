import { useSelector } from 'react-redux'
import { Navigate, Outlet } from 'react-router-dom'

function AdminRoute() {
  const user = useSelector((state) => state.auth.user)

  if (user === null) {
    return (
      <div className="min-h-screen flex items-center justify-center text-sm text-gray-400">Loading…</div>
    )
  }
  if (user.role !== 'admin') {
    return <Navigate to="/" replace />
  }
  return <Outlet />
}

export default AdminRoute
