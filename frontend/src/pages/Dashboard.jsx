import { useEffect, useRef, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Link, useParams } from 'react-router-dom'
import apiClient from '../api/client'
import { fetchAgents } from '../store/slices/agentsSlice'
import { fetchEvents } from '../store/slices/eventsSlice'
import { clearSummary, fetchRunSummary, fetchSimulationStatus, resetSimulationState } from '../store/slices/simulationSlice'
import { fetchPendingTasks } from '../store/slices/tasksSlice'
import SimulationControls from '../components/SimulationControls'
import TaskQueue from '../components/TaskQueue'
import EndOfRunSummary from '../components/EndOfRunSummary'
import AgentMetricChart from '../components/charts/AgentMetricChart'
import { EXECUTIVES } from '../components/boardroom/Boardroom3D'
import { getLatestMessage } from '../components/boardroom/eventRoutes'
import { toChartData } from '../utils/chartData'
import useVisiblePolling from '../hooks/useVisiblePolling'
import '../components/boardroom/boardroom.css'
import './dashboard.css'

const POLL_INTERVAL_MS=1800
const ACCENTS={finance:'#4e977b',marketing:'#b185bb',hr:'#cc8b76',operations:'#bb8e56',ceo:'#c69d59'}
const display=(value)=>value==null?'—':typeof value==='number'?value.toLocaleString():String(value)
const displayEvent=(type)=>String(type||'event').replace(/_/g,' ').replace(/\./g,' • ')
export default function Dashboard(){
 const { businessId }=useParams()
 const dispatch=useDispatch()
 const statuses=useSelector(s=>s.agents.statuses)
 const agentLoad=useSelector(s=>s.agents.loadStatus)
 const agentError=useSelector(s=>s.agents.error)
 const events=useSelector(s=>s.events.items)
 const eventLoad=useSelector(s=>s.events.loadStatus)
 const eventError=useSelector(s=>s.events.error)
 const tasks=useSelector(s=>s.tasks.items)
 const {isRunning,isPaused,runId,tickCount,summary,terminalStatus}=useSelector(s=>s.simulation)
 const [financeHistory,setFinanceHistory]=useState([])
 const [marketingHistory,setMarketingHistory]=useState([])
 const [metricError,setMetricError]=useState(false)
 const [showControls,setShowControls]=useState(true)
 const wasRunning=useRef(false)
 useEffect(()=>{dispatch(resetSimulationState());wasRunning.current=false;setFinanceHistory([]);setMarketingHistory([])},[businessId,dispatch])
 useVisiblePolling(()=>{
   dispatch(fetchAgents(businessId))
   dispatch(fetchSimulationStatus(businessId))
   dispatch(fetchEvents(businessId))
   dispatch(fetchPendingTasks(businessId))
   Promise.all([
     apiClient.get(`/api/businesses/${businessId}/agents/finance/history`,{params:{limit:50}}),
     apiClient.get(`/api/businesses/${businessId}/agents/marketing/history`,{params:{limit:50}})
   ]).then(([finance,marketing])=>{setFinanceHistory(finance.data);setMarketingHistory(marketing.data);setMetricError(false)})
   .catch(()=>setMetricError(true))
 },POLL_INTERVAL_MS,[dispatch,businessId])
 useEffect(()=>{if(wasRunning.current&&!isRunning&&runId)dispatch(fetchRunSummary({businessId,runId}));wasRunning.current=isRunning},[isRunning,runId,businessId,dispatch])
 useEffect(()=>{if(isRunning)dispatch(clearSummary())},[isRunning,dispatch])
 const lastMessage=getLatestMessage(events)
 const status=isRunning?(isPaused?'Paused':'Running'):(terminalStatus||'Idle')
 return <main className="hq-dashboard">
   <header className="hq-page-header">
     <div><span className="hq-kicker">EXECUTIVE COMMAND CENTER / BUSINESS OVERVIEW</span><h1>Your startup at a glance.</h1><p>Understand what your autonomous agents are doing, what they decided, and what happens next.</p></div>
     <div className="hq-header-status"><span className={'hq-status-light '+(isRunning?'running':'')}/><strong>{status}</strong><small>{runId?'Run '+runId.slice(0,8):'No active run'}</small></div>
   </header>
   <div className="hq-kpi-grid">
     <div className="hq-kpi"><span>SIMULATION CYCLE</span><strong>{display(tickCount)}</strong><small>{status}</small></div>
     <div className="hq-kpi"><span>AGENTS CONNECTED</span><strong>{agentLoad==='succeeded'?Object.keys(statuses).length:'—'} <small>/ 5</small></strong><small>From backend snapshot</small></div>
     <div className="hq-kpi"><span>OWNER REVIEWS</span><strong>{display(tasks.length)}</strong><small>Tasks awaiting action</small></div>
     <div className="hq-kpi"><span>RECORDED EVENTS</span><strong>{eventLoad==='succeeded'?display(events.length):'—'}</strong><small>Most recent 100 in memory</small></div>
   </div>
   <section className="hq-control-section"><div className="hq-control-title"><h2>Simulation control</h2><button type="button" onClick={()=>setShowControls(!showControls)}>{showControls?'Collapse':'Expand'} settings</button></div>{showControls&&<SimulationControls businessId={businessId}/>}</section>
   {(agentError||eventError)&&<p className="hq-alert" role="alert">Backend data unavailable or delayed. {agentError||eventError}. Values may be out of date.</p>}
   <section className="hq-command-brief">
     <div><span className="hq-kicker">EXECUTIVE COLLABORATION</span><h2>Your AI team is in session.</h2><p>Follow real agent discussions in the dedicated immersive boardroom. Here you can focus on budgets, tasks, performance and approvals.</p><div className="hq-command-agent-row">{EXECUTIVES.map(agent=><span key={agent.id} className="hq-command-agent-pill"><i style={{background:agent.color}}/>{agent.label}</span>)}</div></div>
     <Link className="hq-command-boardroom-link" to={`/b/${businessId}/boardroom`}>Enter 3D Boardroom <span aria-hidden="true">↗</span></Link>
   </section>
   <div className="hq-bottom-grid">
     <section className="hq-activity"><div className="hq-section-header"><div><span className="hq-kicker">ACTIVITY / TRACEABILITY</span><h2>Agent communications</h2></div><span className="hq-quiet-badge">Backend events · polling</span></div>
       {eventLoad==='loading'&&events.length===0&&<p>Loading event history…</p>}
       {eventLoad==='succeeded'&&events.length===0&&<p>No activity recorded yet. Start a simulation to generate backend events.</p>}
       <div className="hq-activity-scroll">
       {[...events].reverse().slice(0,24).map(event=><div className="hq-event" key={event.event_id}>
         <span className="hq-event-icon" aria-hidden="true">↗</span>
         <div><strong>{displayEvent(event.event_type)}</strong><p>{event.source||'system'}{event.data?.department?' · '+event.data.department:''}</p><details><summary>Inspect event</summary><pre>{JSON.stringify(event.data,null,2)}</pre></details></div>
         <time>{event.timestamp?new Date(event.timestamp).toLocaleTimeString():'—'}</time>
       </div>)}
       </div>
       {lastMessage&&<p className="hq-message-note">Last verified communication: {lastMessage.sender} → {lastMessage.receiver}</p>}
     </section>
     <div className="hq-action-column">
       <section className="hq-review-section"><div className="hq-section-header"><div><span className="hq-kicker">NEXT ACTION</span><h2>Approvals & tasks</h2></div><Link to={`/b/${businessId}/decision-log`}>Decision history ↗</Link></div><TaskQueue businessId={businessId}/></section>
       <section className="hq-mini-agents"><div className="hq-section-header"><h2>Executive roster</h2></div>
         {EXECUTIVES.map(agent=><Link key={agent.id} to={`/b/${businessId}/agents/${agent.id}`} className="hq-roster-link"><span className="hq-roster-dot" style={{background:ACCENTS[agent.id]}}/>{agent.label}<small>{statuses?.[agent.id]?'Available in backend':'No snapshot'}</small></Link>)}
       </section>
     </div>
   </div>
   <section className="hq-analytics"><div className="hq-section-header"><div><span className="hq-kicker">SIMULATION TELEMETRY</span><h2>Business performance</h2></div><span className="hq-quiet-badge">From agent history</span></div>{metricError&&<p className="hq-alert">Could not retrieve one or more business metrics.</p>}
   <div className="hq-chart-grid">
     <AgentMetricChart title="Finance · Budget pool" data={toChartData(financeHistory,'budget_pool')} dataKey="budget_pool" color="#1f6b57" valueFormatter={v=>'$'+Math.round(v/1000)+'k'}/>
     <AgentMetricChart title="Marketing · Customer base" data={toChartData(marketingHistory,'customer_base')} dataKey="customer_base" color="#a88bc7"/>
     <AgentMetricChart title="Marketing · Brand value" data={toChartData(marketingHistory,'brand_value')} dataKey="brand_value" color="#c69d59" valueFormatter={v=>v.toFixed(0)}/>
   </div></section>
   {summary&&<EndOfRunSummary summary={summary}/>}
 </main>
}
