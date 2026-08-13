import { useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Link, useNavigate } from 'react-router-dom'
import { register } from '../store/slices/authSlice'
import ErrorBanner from '../components/ErrorBanner'
import { STATUS } from '../theme/palette'

function Register() {
  const dispatch = useDispatch()
  const navigate = useNavigate()
  const { status, error } = useSelector((state) => state.auth)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    const result = await dispatch(register({ email, password }))
    if (register.fulfilled.match(result)) {
      navigate('/onboarding')
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
          <p className="text-sm text-gray-500 mb-8">Create your account</p>

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
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-offset-0 transition-colors"
                style={{ borderColor: '#e5e7eb', focusRingColor: STATUS.good }}
              />
              <p className="text-xs text-gray-400 mt-1.5">At least 8 characters</p>
            </div>

            <ErrorBanner message={error} />

            <button
              type="submit"
              disabled={status === 'loading'}
              className="w-full py-3 rounded-lg text-white text-sm font-semibold disabled:opacity-50 transition-all hover:shadow-md"
              style={{ backgroundColor: STATUS.good }}
            >
              {status === 'loading' ? 'Creating account…' : 'Create account'}
            </button>
          </form>

          <p className="text-sm text-gray-500 mt-6 text-center">
            Already have an account?{' '}
            <Link to="/login" className="font-medium text-gray-900 underline hover:text-gray-700">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

export default Register
