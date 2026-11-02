import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Link, useParams } from 'react-router-dom'
import { fetchAgents } from '../store/slices/agentsSlice'
import { fetchEvents } from '../store/slices/eventsSlice'
import { fetchPendingTasks } from '../store/slices/tasksSlice'
import { fetchSimulationStatus } from '../store/slices/simulationSlice'
import useVisiblePolling from '../hooks/useVisiblePolling'
import Boardroom3D, { EXECUTIVES } from '../components/boardroom/Boardroom3D'
import { resolveMessage } from '../components/boardroom/eventRoutes'
import '../components/boardroom/boardroom.css'
import './boardroom-page.css'

const titleCase = (value) => String(value || '').replaceAll('_', ' ').replace(/\b\w/g, char => char.toUpperCase())
const describe = (event) => {
  if (event.data?.message && typeof event.data.message === 'string') return event.data.message
  if (event.data?.reason && typeof event.data.reason === 'string') return event.data.reason
  return titleCase(event.event_type)
}
const agentMatch = (task, id) => task.agent === id || String(task.agent || '').startsWith(id + '_')
export default function Boardroom() {
  const { businessId } = useParams()
  const dispatch = useDispatch()
  const statuses = useSelector(state => state.agents.statuses)
  const events = useSelector(state => state.events.items)
  const eventStatus = useSelector(state => state.events.loadStatus)
  const eventError = useSelector(state => state.events.error)
  const tasks = useSelector(state => state.tasks.items)
  const { isRunning, isPaused, tickCount } = useSelector(state => state.simulation)
  const [selected, setSelected] = useState('ceo')
  const [filter, setFilter] = useState('all')
  useEffect(() => { setSelected('ceo'); setFilter('all') }, [businessId])
  useVisiblePolling(() => {
    dispatch(fetchAgents(businessId))
    dispatch(fetchEvents(businessId))
    dispatch(fetchPendingTasks(businessId))
    dispatch(fetchSimulationStatus(businessId))
  }, 1800, [dispatch, businessId])
  const selectedAgent = EXECUTIVES.find(agent => agent.id === selected) || EXECUTIVES[0]
  const assignedTasks = tasks.filter(task => agentMatch(task, selected))
  const communication = [...events].reverse().map(event => ({ event, route: resolveMessage(event) }))
    .filter(({ event, route }) => filter === 'all' || (route ? route.sender === selected || route.receiver === selected : event.source === selected || String(event.source || '').startsWith(selected + '_')))
    .slice(0, 30)
  return <main className="immersive-room">
    <header className="immersive-room-header">
      <div><span className="hq-kicker">VIRTUAL EXECUTIVE HEADQUARTERS / COLLABORATION</span><h1>Inside the AI boardroom.</h1><p>Explore the five executives, inspect their current assignments, and follow communication recorded by the simulator.</p></div>
      <div className="immersive-room-controls"><span className={'room-status '+(isRunning ? 'running' : '')}>{isRunning ? (isPaused ? 'Paused' : 'Simulation running') : 'Simulation not running'}</span><span>Cycle {tickCount ?? '—'}</span><Link to={`/b/${businessId}/dashboard`}>← Command Center</Link></div>
    </header>
    <div className="immersive-room-layout">
      <div className="immersive-room-stage">
        <Boardroom3D selected={selected} onSelect={setSelected} statuses={statuses} events={events}/>
        <div className="immersive-room-roster" aria-label="Select executive">
          {EXECUTIVES.map(agent => <button key={agent.id} type="button" aria-pressed={selected === agent.id} className={selected === agent.id ? 'active' : ''} onClick={() => {setSelected(agent.id);setFilter('selected')}}>
            <span className="room-avatar" style={{background:agent.color}}>{agent.label.charAt(0)}</span><strong>{agent.label}</strong>
          </button>)}
        </div>
      </div>
      <aside className="immersive-room-detail">
        <span className="hq-kicker">EXECUTIVE SPOTLIGHT</span>
        <div className="room-spotlight-heading"><span className="room-spotlight-icon" style={{background:selectedAgent.color}}>{selectedAgent.label.charAt(0)}</span><div><h2>{selectedAgent.label}</h2><p>{statuses?.[selected] ? 'Backend state available' : 'Awaiting backend state'}</p></div></div>
        <h3>Assigned work requiring attention</h3>
        {assignedTasks.length === 0 ? <p className="room-empty">No pending actionable tasks for this agent. Completed work may be visible in its history.</p> :
          <div className="room-tasks">{assignedTasks.slice(0, 8).map(task => <article key={task.id}><span>{titleCase(task.status)}</span><strong>{task.objective || titleCase(task.action_type)}</strong><small>{task.id}</small></article>)}</div>}
        <h3>Backend state</h3>
        {statuses?.[selected] ? <dl className="room-facts">{Object.entries(statuses[selected]).filter(([,value])=>['string','number','boolean'].includes(typeof value)).slice(0,8).map(([key,value])=><div key={key}><dt>{titleCase(key)}</dt><dd>{String(value)}</dd></div>)}</dl> : <p className="room-empty">No agent snapshot available.</p>}
        <Link className="room-open-agent" to={`/b/${businessId}/agents/${selected}`}>Open full agent workspace ↗</Link>
      </aside>
    </div>
    <section className="room-conversation">
      <div className="room-conversation-heading"><div><span className="hq-kicker">SIMULATOR RECORDS</span><h2>Communication & activity timeline</h2><p>Events are retrieved from the backend. A directional arrow appears only when a known agent-to-agent route exists.</p></div><div className="room-filters"><button type="button" aria-pressed={filter==='all'} onClick={()=>setFilter('all')}>All events</button><button type="button" aria-pressed={filter==='selected'} onClick={()=>setFilter('selected')}>{selectedAgent.label} only</button></div></div>
      {eventError && <p role="alert" className="room-empty">Could not refresh events: {eventError}</p>}
      {eventStatus === 'loading' && events.length === 0 && <p className="room-empty">Loading backend events…</p>}
      {communication.length === 0 && eventStatus !== 'loading' && <p className="room-empty">No matching events have been recorded. Start a simulation from the Command Center.</p>}
      <div className="room-event-list">{communication.map(({event,route}) => <article key={event.event_id} className="room-event"><span className="room-event-marker">↗</span><div><strong>{route ? `${titleCase(route.sender)} → ${titleCase(route.receiver)}` : titleCase(event.source || 'System')}</strong><p>{describe(event)}</p><details><summary>Event details</summary><pre>{JSON.stringify(event.data ?? {}, null, 2)}</pre></details></div><time>{event.timestamp ? new Date(event.timestamp).toLocaleTimeString() : '—'}</time></article>)}</div>
    </section>
  </main>
}
