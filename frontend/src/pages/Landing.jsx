import { useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useSelector } from 'react-redux'
import Boardroom3D, { EXECUTIVES } from '../components/boardroom/Boardroom3D'
import '../components/boardroom/boardroom.css'
import './landing.css'

const DESCRIPTIONS = {
  ceo: 'Leads the executive team, reviews proposals and resolves conflicting business priorities.',
  finance: 'Balances resources, evaluates spending and advises on financial decisions.',
  marketing: 'Plans campaigns, evaluates customer growth and initiates budget requests.',
  hr: 'Coordinates hiring, headcount and team morale for the simulated startup.',
  operations: 'Handles resource requests, delivery capacity and operational performance.',
}
const FEATURES = [
  { title: 'Real agent collaboration', icon: '↗', copy: 'Trace requests and decisions between your five autonomous agents.' },
  { title: 'A visible decision process', icon: '◎', copy: 'Inspect CEO reviews, explanations, approvals and the tasks that follow.' },
  { title: 'Business outcomes', icon: '▥', copy: 'See metrics and task progress sourced from the Python simulator.' },
]

export default function Landing() {
  const token = useSelector((state) => state.auth.token)
  const [selected, setSelected] = useState('ceo')
  if (token) return <Navigate to="/app" replace />
  return <main className="marketing-site">
    <section className="marketing-hero" id="home">
      <div className="hero-copy">
        <span className="eyebrow">WELCOME TO THE AI EXECUTIVE HEADQUARTERS</span>
        <h1>Your startup.<br/><em>Five intelligent minds.</em><br/>One command center.</h1>
        <p>Create a virtual company and observe autonomous AI executives plan, collaborate, and make decisions with measurable business outcomes.</p>
        <div className="hero-actions">
          <Link to="/register" className="button-primary">Create your startup <span aria-hidden="true">↗</span></Link>
          <a href="#team" className="button-outline">Meet the executives</a>
        </div>
        <div className="hero-proof"><span>01 / CREATE</span><span>02 / COLLABORATE</span><span>03 / EVALUATE</span></div>
      </div>
      <div className="hero-world">
        <div className="world-caption"><span className="live-dot"/> Interactive 3D preview <small>Illustration only — login to see real events</small></div>
        <Boardroom3D selected={selected} onSelect={setSelected} />
        <div className="hero-world-agent"><span>EXECUTIVE PROFILE</span><strong>{EXECUTIVES.find(a=>a.id===selected)?.label}</strong><p>{DESCRIPTIONS[selected]}</p></div>
      </div>
    </section>
    <section className="marketing-section team-section" id="team">
      <div className="section-heading"><span className="eyebrow">THE LEADERSHIP TEAM</span><h2>Five roles. <em>One shared mission.</em></h2><p>Each executive has a distinct responsibility and a place in your 3D boardroom.</p></div>
      <div className="executive-grid">
        {EXECUTIVES.map(agent=><button type="button" key={agent.id} className={'executive-card '+(selected===agent.id?'executive-card-active':'')} onClick={()=>{setSelected(agent.id);document.getElementById('home')?.scrollIntoView({behavior:'smooth'})}}>
          <span className="executive-card-orbit" style={{background:agent.color}}><span className="executive-card-initial">{agent.label.charAt(0)}</span></span>
          <strong>{agent.label} Agent</strong><p>{DESCRIPTIONS[agent.id]}</p><span className="card-link">Meet agent ↗</span>
        </button>)}
      </div>
    </section>
    <section className="marketing-section steps-section" id="how-it-works">
      <div className="section-heading"><span className="eyebrow">FROM IDEA TO EXECUTION</span><h2>See every decision <em>take shape.</em></h2></div>
      <div className="steps-grid">
        {[
          ['01','Set the scene','Describe your startup, business goals and operating context.'],
          ['02','Bring the team together','Your executive agents receive tasks and analyze business conditions.'],
          ['03','Watch decisions travel','Messages, CEO reviews and next steps appear in your Command Center.'],
          ['04','Measure the outcome','Follow actual simulation metrics and inspect decision history.'],
        ].map(([n,t,c])=><article key={n} className="step-card"><span>{n}</span><h3>{t}</h3><p>{c}</p></article>)}
      </div>
    </section>
    <section className="marketing-section feature-section" id="features">
      <div className="section-heading"><span className="eyebrow">A DIFFERENT KIND OF DASHBOARD</span><h2>Intelligence you can <em>actually inspect.</em></h2></div>
      <div className="feature-grid">{FEATURES.map(f=><article key={f.title} className="feature-tile"><span className="feature-icon">{f.icon}</span><h3>{f.title}</h3><p>{f.copy}</p></article>)}</div>
      <div className="product-preview">
        <div><span className="eyebrow">INSIDE THE COMMAND CENTER</span><h3>From agent conversation to business action.</h3><p>Switch between the 3D boardroom, task approvals and event history. The interface reads your simulator’s results instead of inventing activity.</p><Link to="/register" className="button-outline">Explore the experience ↗</Link></div>
        <div className="preview-card"><div className="preview-bar"><span>● ● ●</span><span>COMMAND CENTER</span></div><div className="preview-stat-row"><div><small>Executive agents</small><strong>5</strong></div><div><small>Event history</small><strong>Traceable</strong></div></div><div className="preview-message"><span>MARKETING</span> Proposal submitted <b>→ FINANCE</b></div><div className="preview-message"><span>FINANCE</span> Budget review <b>→ CEO</b></div><div className="preview-message"><span>CEO</span> Decision recorded <b>✓</b></div><small className="preview-disclaimer">Illustrative workflow, not live simulator data.</small></div>
      </div>
    </section>
    <section className="marketing-cta"><span className="eyebrow">THE NEXT MOVE IS YOURS</span><h2>A new way to experience business leadership.</h2><p>Build a virtual startup, guide your executive team and learn from every decision.</p><Link className="button-champagne" to="/register">Launch your simulation ↗</Link></section>
    <footer className="marketing-footer"><span>Autonomous Startup Simulator</span><span>Five agents · One shared workspace</span><Link to="/login">Sign in</Link></footer>
  </main>
}
