import { useEffect, useRef, useState } from 'react'
import * as THREE from 'three'
import { AGENTS, observedChanges, previewTransfers } from '../../studio/model.mjs'
import { createStudio } from '../../studio/scene.mjs'
import { getLatestMessage } from './eventRoutes'
import './boardroom.css'

export const EXECUTIVES = AGENTS
export default function Boardroom3D({ statuses = {}, events = [], tasks = [], ready = true, onSelect = () => {}, selected = 'ceo', showApprovalLabel = false }) {
  const canvas = useRef(null), labels = useRef(null), engine = useRef(null)
  const select = useRef(onSelect); select.current = onSelect
  const [mode, setMode] = useState('3d'), [error, setError] = useState(''), [preview, setPreview] = useState(false)
  const [handoff, setHandoff] = useState(null)
  const previous = useRef(null), seen = useRef(undefined)
  const lastMessage = getLatestMessage(events)
  useEffect(() => {
    if (mode !== '3d') return
    try {
      const motion = window.matchMedia('(prefers-reduced-motion: reduce)')
      engine.current = createStudio(THREE, canvas.current, {
        reducedMotion: motion.matches,
        onSelect: id => select.current(id),
        onProject: positions => {for(const [id,[x,y]] of Object.entries(positions)){
          const node=labels.current?.querySelector(`[data-agent="${id}"]`)
          if(node)node.style.transform=`translate(${x}px, ${y}px) translate(-50%, -50%)`
        }},
      })
      setError('')
    } catch {setError('3D is unavailable. Use the team list to inspect your executives.')}
    return () => {engine.current?.dispose();engine.current=null}
  }, [mode])
  useEffect(() => {engine.current?.select(selected)}, [selected, mode])
  useEffect(() => {
    if(!ready)return
    const changes=observedChanges(previous.current,tasks)
    previous.current=new Map(tasks.map(t=>[t.id,t]))
    if(changes.length&&!preview)setHandoff(changes.at(-1))
  }, [tasks,ready,preview])
  useEffect(() => {
    const message=lastMessage
    if(seen.current===undefined){if(ready)seen.current=message?.id||null;return}
    if(!message||message.id===seen.current)return
    seen.current=message.id
    if(!preview)setHandoff({...message,label:message.type,source:'backend'})
  }, [lastMessage?.id, ready, preview]) // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(()=>{
    if(!preview)return
    const rows=previewTransfers();let index=0;setHandoff(rows[0])
    const timer=setInterval(()=>{index=(index+1)%rows.length;setHandoff(rows[index])},3900)
    return()=>clearInterval(timer)
  },[preview])
  useEffect(()=>{engine.current?.playTransfer(handoff)},[handoff, mode])
  return <section className="boardroom-shell" aria-label="AI executive boardroom">
    <div className="boardroom-toolbar"><div><strong>Executive floor</strong><span>{preview?'Visual preview · synthetic · no tasks created':'Select an avatar. Inspect real work. Keep approval in your hands.'}</span></div><div className="boardroom-controls"><button onClick={()=>{setPreview(!preview);if(preview)setHandoff(null)}}>{preview?'Exit preview':'Preview handoff'}</button><button onClick={()=>setMode(mode==='3d'?'list':'3d')}>{mode==='3d'?'Team list':'3D view'}</button></div></div>
    {mode==='3d'?<div className="boardroom-canvas"><canvas ref={canvas} aria-label="3D executive avatars; drag to orbit or use the labelled selection buttons"/>{error?<p role="alert" className="boardroom-render-error">{error}<button onClick={()=>setMode('list')}>Open team list</button></p>:<div className="boardroom-projected-labels" ref={labels}>{AGENTS.map(a=><button data-agent={a.id} key={a.id} aria-label={`Select ${a.label}`} aria-pressed={selected===a.id} onClick={()=>onSelect(a.id)}>{a.label}</button>)}{showApprovalLabel && <span data-agent="owner">You · Approval desk</span>}</div>}</div>:<div className="boardroom-list">{AGENTS.map(a=><button key={a.id} onClick={()=>onSelect(a.id)} aria-pressed={selected===a.id}><span style={{background:a.color}}/>{a.label}<small>{statuses[a.id]?'State available':'No snapshot'}</small></button>)}</div>}
    <p className="boardroom-note" role="status">{handoff?`${handoff.source==='visual preview'?'Visual preview: ':''}${handoff.sender.toUpperCase()} → ${handoff.receiver.toUpperCase()} · ${handoff.label}`:'No new handoff. Historical tasks are not replayed as live activity.'}</p>
  </section>
}
