import { useDispatch, useSelector } from 'react-redux'
import { Link, Outlet, useNavigate, useParams } from 'react-router-dom'
import { logout } from '../store/slices/authSlice'
import { clearBusinesses } from '../store/slices/businessSlice'
import BusinessSwitcher from './BusinessSwitcher'
import { STATUS } from '../theme/palette'

const AGENT_LINKS = [
  { key: 'finance', label: 'Finance' },
  { key: 'marketing', label: 'Marketing' },
  { key: 'hr', label: 'HR' },
  { key: 'operations', label: 'Operations' },
  { key: 'ceo', label: 'CEO' },
]

function Layout() {
  const { businessId } = useParams()
  const dispatch = useDispatch()
  const navigate = useNavigate()
  const isAdmin = useSelector((state) => state.auth.user?.role === 'admin')

  const handleLogout = () => {
    dispatch(logout())
    dispatch(clearBusinesses())
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <aside className="w-56 bg-white border-r border-gray-200 flex flex-col shrink-0">
        <div className="px-4 py-5 border-b border-gray-100">
          <h1 className="text-lg font-bold text-gray-900">Startup Simulator</h1>
        </div>

        <div className="px-4 py-3 border-b border-gray-100">
          <BusinessSwitcher />
        </div>

        <nav className="flex-1 px-2 py-3 space-y-1">
          <Link
            to={`/b/${businessId}/dashboard`}
            className="block px-3 py-2 rounded text-sm font-medium text-gray-700 hover:bg-gray-100"
          >
            Dashboard
          </Link>
          <p className="px-3 pt-3 pb-1 text-xs font-semibold text-gray-400 uppercase">Agents</p>
          {AGENT_LINKS.map((agent) => (
            <Link
              key={agent.key}
              to={`/b/${businessId}/agents/${agent.key}`}
              className="block px-3 py-2 rounded text-sm font-medium text-gray-700 hover:bg-gray-100"
            >
              {agent.label}
            </Link>
          ))}
          <Link
            to={`/b/${businessId}/memory-inspector`}
            className="block px-3 py-2 mt-2 rounded text-sm font-medium text-gray-700 hover:bg-gray-100 border-t border-gray-100 pt-3"
          >
            Memory Inspector
          </Link>
        </nav>

        <div className="px-4 py-4 border-t border-gray-100 space-y-2">
          {isAdmin && (
            <Link
              to="/admin"
              className="block text-sm font-medium text-gray-500 hover:text-gray-700"
            >
              Admin →
            </Link>
          )}
          <button
            type="button"
            onClick={handleLogout}
            className="w-full text-sm font-medium py-2 rounded hover:bg-gray-50"
            style={{ color: STATUS.critical }}
          >
            Log out
          </button>
        </div>
      </aside>

      <div className="flex-1 min-w-0">
        <Outlet />
      </div>
    </div>
  )
}

export default Layout
