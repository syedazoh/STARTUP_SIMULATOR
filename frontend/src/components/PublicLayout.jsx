import './public-layout.css'
import { NavLink, Outlet } from 'react-router-dom'

export default function PublicLayout() {
  return <div className="public-app">
    <header className="public-header">
      <NavLink to="/" className="public-brand"><span className="public-brand-mark">✦</span><span>Startup Simulator<small>Autonomous executive workspace</small></span></NavLink>
      <nav aria-label="Public navigation">
        <a href="/#executives">The team</a><a href="/#process">How it works</a><NavLink to="/getting-started">Product demo</NavLink>
        <NavLink to="/login" className="public-signin">Sign in</NavLink>
        <NavLink to="/register" className="public-register">Start simulation ↗</NavLink>
      </nav>
    </header>
    <Outlet />
  </div>
}
