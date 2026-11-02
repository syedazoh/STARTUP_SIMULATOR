import './public-layout.css'
import { NavLink, Outlet } from 'react-router-dom'

export default function PublicLayout() {
  return <div className="public-app">
    <header className="public-header">
      <NavLink to="/" className="public-brand"><span className="public-brand-mark">✦</span><span>Startup Simulator<small>Autonomous executive workspace</small></span></NavLink>
      <nav aria-label="Public navigation">
        <a href="/#team">The team</a><a href="/#how-it-works">How it works</a><a href="/#features">Features</a>
        <NavLink to="/login" className="public-signin">Sign in</NavLink>
        <NavLink to="/register" className="public-register">Start simulation ↗</NavLink>
      </nav>
    </header>
    <Outlet />
  </div>
}
