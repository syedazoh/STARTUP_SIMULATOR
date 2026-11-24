import FooterSculpture from '../appearance/FooterSculpture'
import {useAppearance} from '../appearance/Appearance'
import Atmosphere from '../landing/Atmosphere';
import { useEffect, useLayoutEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Link, NavLink, Outlet, useNavigate, useParams } from 'react-router-dom'
import { logout } from '../store/slices/authSlice'
import { clearBusinesses, setActiveBusiness } from '../store/slices/businessSlice'
import BusinessSwitcher from './BusinessSwitcher'
import './layout.css'

const loadThree=()=>import('three')
const agentLinks=[['ceo','CEO'],['finance','Finance'],['marketing','Marketing'],['hr','HR'],['operations','Operations']]
const primary=[['dashboard','◫','Command Center'],['boardroom','◉','3D Boardroom'],['decision-log','☷','Decision History'],['memory-inspector','◇','Agent Memory'],['profile','▤','Business Profile']]
export default function Layout(){
 const { businessId }=useParams()
 const {preferences,theme}=useAppearance()
 const dispatch=useDispatch()
 const navigate=useNavigate()
 const [open,setOpen]=useState(false)
 const [backgroundMotion,setBackgroundMotion]=useState(true),[reduced,setReduced]=useState(false)
 useEffect(()=>{const preference=matchMedia('(prefers-reduced-motion: reduce)');setReduced(preference.matches);try{setBackgroundMotion(localStorage.getItem('startup-workspace-motion')!=='off')}catch{}const update=()=>setReduced(preference.matches);preference.addEventListener('change',update);return()=>preference.removeEventListener('change',update)},[])
 const logoutError=useSelector(s=>s.auth.error)
 const isAdmin=useSelector(s=>s.auth.user?.role==='admin')
 useLayoutEffect(()=>{dispatch(setActiveBusiness(businessId));setOpen(false)},[businessId,dispatch])
 const doLogout=async()=>{const result=await dispatch(logout());if(!logout.fulfilled.match(result))return;dispatch(clearBusinesses());navigate('/login')}
 return <div className="hq-app-shell">
   <button className="hq-mobile-trigger" aria-expanded={open} aria-controls="hq-nav" onClick={()=>setOpen(!open)} type="button">{open?'Close menu':'☰ Menu'}</button>
   {open&&<button className="hq-mobile-scrim" onClick={()=>setOpen(false)} aria-label="Close navigation" type="button"/>}
   <aside id="hq-nav" className={'hq-sidebar '+(open?'hq-sidebar-open':'')}>
     <Link to={`/b/${businessId}/dashboard`} className="hq-brand" onClick={()=>setOpen(false)}><span>✦</span><div><strong>Startup Simulator</strong><small>EXECUTIVE HEADQUARTERS</small></div></Link>
     <div className="hq-switcher"><BusinessSwitcher/></div>
     <nav aria-label="Workspace navigation">
       <small className="hq-nav-heading">WORKSPACE</small>
       {primary.map(([route,icon,label])=><NavLink key={route} to={`/b/${businessId}/${route}`} end={route==='dashboard'} className={({isActive})=>'hq-nav-link '+(isActive?'active':'')} onClick={()=>setOpen(false)}><span aria-hidden="true">{icon}</span>{label}</NavLink>)}
       <small className="hq-nav-heading hq-nav-agents">EXECUTIVE AGENTS</small>
       {agentLinks.map(([key,label])=><NavLink key={key} to={`/b/${businessId}/agents/${key}`} className={({isActive})=>'hq-nav-link '+(isActive?'active':'')} onClick={()=>setOpen(false)}><span aria-hidden="true" className={'hq-agent-dot hq-'+key}/>{label}</NavLink>)}
     </nav>
     <div className="hq-sidebar-footer"><Link to="/getting-started">Product demo &amp; quick start</Link>{isAdmin&&<Link to="/admin">Admin workspace ↗</Link>}<button type="button" onClick={doLogout}>Sign out ↗</button>{logoutError&&<p role="alert">{logoutError}</p>}</div>
   </aside>
   <div className="hq-workspace"><div className="classic-workspace-effects"><Atmosphere loadThree={loadThree} enabled={backgroundMotion&&preferences.motion&&!reduced} theme={theme}/></div><Outlet key={businessId}/><footer className="classic-workspace-footer"><FooterSculpture loadThree={loadThree}/><div><Link to={`/b/${businessId}/dashboard`}>Startup Simulator</Link><h2>Your direction.<br/><em>A whole team behind it.</em></h2><p>Open the proposal, make the decision, then follow the recorded result.</p></div><nav aria-label="Workspace footer"><Link to={`/b/${businessId}/dashboard`}>Command center</Link><Link to={`/b/${businessId}/boardroom`}>3D Boardroom</Link><Link to={`/b/${businessId}/agents/ceo`}>CEO workspace</Link><Link to="/getting-started">Video & written guide</Link></nav></footer><button className="classic-motion-toggle" disabled={reduced||!preferences.motion} aria-pressed={backgroundMotion&&preferences.motion&&!reduced} onClick={()=>{setBackgroundMotion(!backgroundMotion);try{localStorage.setItem('startup-workspace-motion',backgroundMotion?'off':'on')}catch{}}}>Background motion {backgroundMotion&&preferences.motion&&!reduced?'on':'off'}</button></div>
 </div>
}
