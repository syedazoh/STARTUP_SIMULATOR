'use client';
import {useEffect, useRef, useState, type FormEvent} from 'react';
import {readRuns, runCommand} from './actions';
type Citation = {document_id: string; version: number; title: string; quote: string};
type Result = {mode: string; summary: string; reasoning: string; artifact: string; recommended_budget_minor?: number; citations: Citation[]};
type Run = {run_id: string; status: string; market_opportunity: string; currency: string; report: string; task_id?: string; task_status?: string; recorded_outcome?: unknown; roles: {role: string; job_id: string; event_id: string; status: string; attempts: number; error?: string; result?: Result}[]};
export default function Runs({businessId, initial}: {businessId: string; initial: Run[]}) {
  const [runs, setRuns] = useState(initial), [error, setError] = useState(''), [busy, setBusy] = useState(false);
  const generation = useRef(0), mounted = useRef(true), key = useRef('');
  const base = `/workspace/${encodeURIComponent(businessId)}`;
  async function refresh() {
    const request = ++generation.current;
    try {const next = await readRuns(businessId); if(mounted.current && request === generation.current) {setRuns(next); setError('');}}
    catch {if(mounted.current && request === generation.current) setError('Could not refresh. Saved results remain visible; check the backend and retry.');}
  }
  useEffect(() => {
    mounted.current = true;
    let timer: ReturnType<typeof setTimeout>;
    let active = true;
    async function poll() {if(!active)return; if(!document.hidden) await refresh(); if(active)timer=setTimeout(poll, 3000);}
    timer=setTimeout(poll, 3000);
    return () => {active=false; mounted.current=false; generation.current++; clearTimeout(timer);};
  }, [businessId]); // Completion order is guarded; poll requests do not overlap.
  async function command(command: string, payload: Record<string, unknown> = {}, runId = '') {
    setBusy(true);setError('');generation.current++;
    try {await runCommand(businessId, command, payload, runId); if(command==='submit')key.current=''; await refresh();}
    catch(e) {setError(e instanceof Error ? e.message : 'Request failed. Refresh before retrying.');}
    finally {setBusy(false);}
  }
  function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault(); const data = new FormData(e.currentTarget);
    key.current ||= crypto.randomUUID();
    void command('submit', {idempotency_key: key.current, seed: Number(data.get('seed')), goal: String(data.get('goal')), requested_budget_minor: Number(data.get('budget')), ticket: String(data.get('ticket'))});
  }
  return <main>
    <a href={base}>← Command center</a>
    <h1>Seven-role launch simulation</h1>
    <p>Synthetic scenario · rule-based recommendations · separate worker processes required. No email, post or real payment is sent.</p>
    <section className="card"><h2>Start a bounded launch</h2>
      <p>Workers: CEO → Marketing → Finance → HR → Operations → Support → Strategy. Analysis runs for at most ten minutes; campaign execution requires your separate approval.</p>
      <form onSubmit={submit}>
        <label>Goal<input name="goal" defaultValue="Launch a sustainable product campaign" maxLength={1000} required/></label>
        <label>Seed<input name="seed" type="number" min="0" max="2147483647" defaultValue="17" required/></label>
        <label>Requested budget (USD cents)<input name="budget" type="number" min="1" max="10000000000" defaultValue="500000" required/></label>
        <label>Synthetic support ticket<input name="ticket" defaultValue="What is the product launch return policy?" maxLength={1000} required/></label>
        <button disabled={busy}>Start synthetic analysis</button>
      </form>
      <p>Support needs an authorized policy document. <a href={`${base}/automation`}>Upload knowledge sources</a>; select Support. Otherwise the response explicitly abstains.</p>
    </section>
    <p role="status">{busy?'Saving request…':'Progress refreshes every 3 seconds while this tab is visible.'}</p>
    {error && <p role="alert" className="error">{error}</p>}
    <button disabled={busy} onClick={()=>void refresh()}>Refresh analyses</button>
    <p><a href={`${base}/evidence?format=json`}>Download evidence JSON</a> · <a href={`${base}/evidence?format=csv`}>Download evidence CSV</a></p>
    <p>Downloads contain the latest 500 allowlisted records across decisions, events, tasks and role jobs. JSON includes a truncation flag; downloads are not complete backups.</p>
    {!runs.length && <p>No analyses yet. Start a scenario after launching the role workers.</p>}
    {runs.map(run=><section className="card" key={run.run_id}>
      <h2>Launch analysis · {run.status.replaceAll('_',' ')}</h2>
      <p>{run.market_opportunity}</p><p><small>Run {run.run_id}</small></p>
      <ol>{run.roles.map(row=><li key={row.role}>
        <h3>{row.role.toUpperCase()} · {row.status.replaceAll('_',' ')}</h3>
        <p>Attempts: {row.attempts}{row.error?` · ${row.error}`:''}</p>
        {row.result && <><p>{row.result.summary}</p><p><strong>Mode: {row.result.mode}</strong></p>
          <p>{row.result.reasoning}</p><p style={{whiteSpace:'pre-wrap'}}>{row.result.artifact}</p>
          {typeof row.result.recommended_budget_minor === 'number' && <p>Recommended ceiling: {row.result.recommended_budget_minor} {run.currency} cents</p>}
          {row.result.citations.map(c=><blockquote key={`${c.document_id}-${c.version}`}><p>{c.quote}</p><cite>{c.title} · version {c.version} · {c.document_id}</cite></blockquote>)}
        </>}
      </li>)}</ol>
      <p>{run.report}</p>
      {run.status==='running' && <button disabled={busy} onClick={()=>void command('cancel',{},run.run_id)}>Cancel this analysis</button>}
      {run.status==='ready_for_review' && !run.task_id && <button disabled={busy} onClick={()=>void command('proposal',{},run.run_id)}>Create campaign for owner review</button>}
      {run.task_id && <p>Campaign: {run.task_status} · <a href={base}>Review campaign in command center</a></p>}
      {Boolean(run.recorded_outcome) && <details><summary>Saved execution outcome</summary><pre>{JSON.stringify(run.recorded_outcome,null,2)}</pre></details>}
    </section>)}
  </main>;
}
