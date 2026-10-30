import { useDispatch, useSelector } from 'react-redux'
import { Link, Outlet, useNavigate } from 'react-router-dom'
import { logout } from '../store/slices/authSlice'
import { clearBusinesses } from '../store/slices/businessSlice'
import { STATUS } from '../theme/palette'

function AdminLayout() {
  const dispatch = useDispatch()
  const navigate = useNavigate()
  const logoutError = useSelector((state) => state.auth.error)

  const handleLogout = async () => {
    const result = await dispatch(logout())
    if (!logout.fulfilled.match(result)) return
    dispatch(clearBusinesses())
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <aside className="w-56 bg-white border-r border-gray-200 flex flex-col shrink-0">
        <div className="px-4 py-5 border-b border-gray-100">
          <h1 className="text-lg font-bold text-gray-900">Admin</h1>
        </div>

        <nav className="flex-1 px-2 py-3 space-y-1">
          <Link to="/admin" className="block px-3 py-2 rounded text-sm font-medium text-gray-700 hover:bg-gray-100">
            Overview
          </Link>
          <Link
            to="/admin/businesses"
            className="block px-3 py-2 rounded text-sm font-medium text-gray-700 hover:bg-gray-100"
          >
            Businesses
          </Link>
          <Link
            to="/admin/system-health"
            className="block px-3 py-2 rounded text-sm font-medium text-gray-700 hover:bg-gray-100"
          >
            System Health
          </Link>
        </nav>

        <div className="px-4 py-4 border-t border-gray-100 space-y-2">
          <Link to="/" className="block text-sm font-medium text-gray-500 hover:text-gray-700">
            ← Back to app
          </Link>
          <button
            type="button"
            onClick={handleLogout}
            className="w-full text-sm font-medium py-2 rounded hover:bg-gray-50"
            style={{ color: STATUS.critical }}
          >
            Log out
          </button>
          {logoutError && <p role="alert" className="text-xs text-red-600">{logoutError}</p>}
        </div>
      </aside>

      <div className="flex-1 min-w-0">
        <Outlet />
      </div>
    </div>
  )
}

export default AdminLayout
