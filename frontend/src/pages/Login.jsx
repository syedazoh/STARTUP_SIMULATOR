import { useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Link, useNavigate } from 'react-router-dom'
import { login } from '../store/slices/authSlice'
import ErrorBanner from '../components/ErrorBanner'
import { STATUS } from '../theme/palette'

function Login() {
  const dispatch = useDispatch()
  const navigate = useNavigate()
  const { status, error } = useSelector((state) => state.auth)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    const result = await dispatch(login({ email, password }))
    if (login.fulfilled.match(result)) {
      navigate('/')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 lg:py-20">
      <div className="max-w-md mx-auto px-4">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 sm:p-8">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">🚀</span>
            <h1 className="text-xl font-bold text-gray-900">Startup Simulator</h1>
          </div>
          <p className="text-sm text-gray-500 mb-8">Sign in to your account</p>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-xs text-gray-500 mb-1.5" htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-offset-0 transition-colors"
                style={{ borderColor: '#e5e7eb', focusRingColor: STATUS.good }}
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1.5" htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-offset-0 transition-colors"
                style={{ borderColor: '#e5e7eb', focusRingColor: STATUS.good }}
              />
            </div>

            <ErrorBanner message={error} />

            <button
              type="submit"
              disabled={status === 'loading'}
              className="w-full py-3 rounded-lg text-white text-sm font-semibold disabled:opacity-50 transition-all hover:shadow-md"
              style={{ backgroundColor: STATUS.good }}
            >
              {status === 'loading' ? 'Signing in…' : 'Sign in'}
            </button>
          </form>

          <p className="text-sm text-gray-500 mt-6 text-center">
            Don't have an account?{' '}
            <Link to="/register" className="font-medium text-gray-900 underline hover:text-gray-700">
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

export default Login
