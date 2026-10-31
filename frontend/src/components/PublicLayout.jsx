import { Link, Outlet } from 'react-router-dom'
import { useSelector } from 'react-redux'
import { STATUS } from '../theme/palette'

const AGENT_LINKS = [
  { key: 'finance', label: 'Finance Agent', description: 'Budgets, revenue, expenses' },
  { key: 'marketing', label: 'Marketing Agent', description: 'Campaigns, market analysis' },
  { key: 'hr', label: 'HR Agent', description: 'Recruitment, payroll, performance' },
  { key: 'operations', label: 'Operations Agent', description: 'Supply chain, resources' },
  { key: 'ceo', label: 'CEO Agent', description: 'Strategy, coordination, vision' },
]

export default function PublicLayout() {
  const { token, user } = useSelector((state) => state.auth)
  const isAuthenticated = !!token && !!user

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col shrink-0 hidden lg:block">
        <div className="px-4 py-6 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🚀</span>
            <h1 className="text-lg font-bold text-gray-900">Startup Simulator</h1>
          </div>
          <p className="text-xs text-gray-500 mt-1">AI-Powered Business Simulation</p>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          <p className="px-3 pt-2 pb-1 text-xs font-semibold text-gray-400 uppercase">Agents</p>
          {AGENT_LINKS.map((agent) => (
            <div
              key={agent.key}
              className="px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors cursor-default"
            >
              <p className="text-sm font-medium text-gray-900">{agent.label}</p>
              <p className="text-xs text-gray-500 mt-0.5">{agent.description}</p>
            </div>
          ))}

          <div className="mt-4 pt-4 border-t border-gray-100">
            <p className="px-3 pb-1 text-xs font-semibold text-gray-400 uppercase">Features</p>
            <div className="px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors cursor-default">
              <p className="text-sm font-medium text-gray-900">Multi-Agent Collaboration</p>
              <p className="text-xs text-gray-500 mt-0.5">5 autonomous AI agents</p>
            </div>
            <div className="px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors cursor-default">
              <p className="text-sm font-medium text-gray-900">Real-time Decisions</p>
              <p className="text-xs text-gray-500 mt-0.5">Watch agents decide live</p>
            </div>
            <div className="px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors cursor-default">
              <p className="text-sm font-medium text-gray-900">Persistent Memory</p>
              <p className="text-xs text-gray-500 mt-0.5">Agents learn over time</p>
            </div>
          </div>
        </nav>

        <div className="px-4 py-4 border-t border-gray-100 space-y-2">
          {isAuthenticated ? (
            <>
              <Link
                to="/app"
                className="block text-sm font-medium text-gray-500 hover:text-gray-700"
              >
                → Dashboard
              </Link>
              <button
                type="button"
                className="w-full text-sm font-medium py-2 rounded hover:bg-gray-50 text-left"
                style={{ color: STATUS.critical }}
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <Link
                to="/login"
                className="block w-full text-center py-2.5 rounded-lg font-medium text-white transition-all"
                style={{ backgroundColor: STATUS.good }}
              >
                Sign In
              </Link>
              <Link
                to="/register"
                className="block w-full text-center py-2.5 rounded-lg font-medium border border-gray-300 text-gray-700 hover:bg-gray-50 transition-all"
              >
                Create Account
              </Link>
            </>
          )}
        </div>
      </aside>

      <div className="flex-1 min-w-0 lg:pl-0">
        <Outlet />
      </div>
    </div>
  )
}