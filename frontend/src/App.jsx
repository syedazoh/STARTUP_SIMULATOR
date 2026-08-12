import { useEffect } from 'react'
import { useDispatch } from 'react-redux'
import { BrowserRouter, Navigate, Route, Routes, useNavigate } from 'react-router-dom'
import { setOnUnauthorized } from './api/client'
import { logout } from './store/slices/authSlice'
import ProtectedRoute from './components/ProtectedRoute'
import RequireBusiness from './components/RequireBusiness'
import HomeRedirect from './components/HomeRedirect'
import Layout from './components/Layout'
import AdminRoute from './components/AdminRoute'
import AdminLayout from './components/AdminLayout'
import Login from './pages/Login'
import Register from './pages/Register'
import Onboarding from './pages/Onboarding'
import Dashboard from './pages/Dashboard'
import AgentDetail from './pages/AgentDetail'
import AdminOverview from './pages/AdminOverview'
import AdminBusinesses from './pages/AdminBusinesses'
import AdminBusinessDetail from './pages/AdminBusinessDetail'
import AdminSystemHealth from './pages/AdminSystemHealth'

function UnauthorizedHandler() {
  const dispatch = useDispatch()
  const navigate = useNavigate()

  useEffect(() => {
    setOnUnauthorized(() => {
      dispatch(logout())
      navigate('/login')
    })
  }, [dispatch, navigate])

  return null
}

function App() {
  return (
    <BrowserRouter>
      <UnauthorizedHandler />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        <Route element={<ProtectedRoute />}>
          <Route path="/onboarding" element={<Onboarding />} />

          <Route element={<RequireBusiness />}>
            <Route path="/" element={<HomeRedirect />} />
            <Route element={<Layout />}>
              <Route path="/b/:businessId/dashboard" element={<Dashboard />} />
              <Route path="/b/:businessId/agents/:agentKey" element={<AgentDetail />} />
            </Route>
          </Route>

          <Route element={<AdminRoute />}>
            <Route element={<AdminLayout />}>
              <Route path="/admin" element={<AdminOverview />} />
              <Route path="/admin/businesses" element={<AdminBusinesses />} />
              <Route path="/admin/businesses/:businessId" element={<AdminBusinessDetail />} />
              <Route path="/admin/system-health" element={<AdminSystemHealth />} />
            </Route>
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
