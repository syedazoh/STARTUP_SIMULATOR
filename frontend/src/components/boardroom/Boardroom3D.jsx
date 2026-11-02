import { Suspense, useEffect, useMemo, useState } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Html, OrbitControls, RoundedBox } from '@react-three/drei'
import * as THREE from 'three'

export const EXECUTIVES = [
  { id: 'ceo', label: 'CEO', color: '#c69d59', position: [0, 0, -2.4] },
  { id: 'finance', label: 'Finance', color: '#4e977b', position: [-2.8, 0, -0.6] },
  { id: 'marketing', label: 'Marketing', color: '#b185bb', position: [2.8, 0, -0.6] },
  { id: 'hr', label: 'HR', color: '#cc8b76', position: [-2.3, 0, 2.3] },
  { id: 'operations', label: 'Operations', color: '#bb8e56', position: [2.3, 0, 2.3] },
]

const positionOf = (id) => EXECUTIVES.find((agent) => agent.id === id)?.position

function Person({ agent, active, selected, onSelect }) {
  const [x, , z] = agent.position
  const [hovered, setHovered] = useState(false)
  const focus = active || selected || hovered
  return (
    <group position={[x, 0, z]} onClick={(e) => { e.stopPropagation(); onSelect(agent.id) }}
      onPointerOver={(e) => { e.stopPropagation(); setHovered(true); document.body.style.cursor = 'pointer' }}
      onPointerOut={() => { setHovered(false); document.body.style.cursor = '' }}>
      <mesh position={[0, 0.16, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <torusGeometry args={[0.7, 0.035, 8, 48]} />
        <meshStandardMaterial color={agent.color} emissive={agent.color} emissiveIntensity={focus ? 0.8 : 0.12} />
      </mesh>
      <mesh position={[0, 0.72, 0]} castShadow><cylinderGeometry args={[0.44, 0.51, 0.95, 16]} />
        <meshStandardMaterial color={agent.color} roughness={0.75} />
      </mesh>
      <mesh position={[0, 1.47, 0]} castShadow><sphereGeometry args={[0.37, 24, 16]} />
        <meshStandardMaterial color="#dfb692" roughness={0.8} />
      </mesh>
      <mesh position={[0, 1.73, -0.08]} castShadow><sphereGeometry args={[0.37, 24, 12, 0, Math.PI * 2, 0, Math.PI / 2.2]} />
        <meshStandardMaterial color="#473932" roughness={0.85} />
      </mesh>
      {[-1, 1].map((side) => <mesh key={side} position={[side * 0.47, 0.91, 0]} rotation={[0, 0, side * 0.24]} castShadow>
        <capsuleGeometry args={[0.15, 0.54, 6, 12]} /><meshStandardMaterial color={agent.color} />
      </mesh>)}
      <mesh position={[0, 0.93, 0.455]}><boxGeometry args={[0.13, 0.3, 0.03]} />
        <meshStandardMaterial color="#f2e1bf" />
      </mesh>
      <Html position={[0, 2.17, 0]} center distanceFactor={11} style={{ pointerEvents: 'none' }}>
        <div className="boardroom-agent-label" style={{ borderColor: agent.color }}>{agent.label}{active ? ' • Active' : ''}</div>
      </Html>
    </group>
  )
}

function CommunicationBeam({ sender, receiver }) {
  const start = positionOf(sender), end = positionOf(receiver)
  const [phase, setPhase] = useState(0)
  useFrame((_, delta) => setPhase((value) => (value + delta * 0.55) % 1))
  const points = useMemo(() => {
    if (!start || !end || sender === receiver) return null
    return new THREE.QuadraticBezierCurve3(
      new THREE.Vector3(start[0], 1.7, start[2]),
      new THREE.Vector3((start[0] + end[0]) / 2, 3, (start[2] + end[2]) / 2),
      new THREE.Vector3(end[0], 1.7, end[2])
    )
  }, [start, end, sender, receiver])
  if (!points) return null
  const path = points.getPoints(40)
  return <group>
    <mesh>
      <tubeGeometry args={[points, 40, 0.025, 6, false]} />
      <meshBasicMaterial color="#a88bc7" transparent opacity={0.72} />
    </mesh>
    <mesh position={points.getPoint(phase).toArray()}>
      <sphereGeometry args={[0.11, 12, 12]} />
      <meshBasicMaterial color="#ead2ff" />
    </mesh>
  </group>
}

function Scene({ statuses, selected, onSelect, message }) {
  return <>
    <color attach="background" args={['#e8eee6']} />
    <ambientLight intensity={1.7} />
    <directionalLight position={[3, 8, 4]} intensity={2.2} castShadow shadow-mapSize={[1024, 1024]} />
    <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow><planeGeometry args={[30, 30]} /><meshStandardMaterial color="#dde7db" /></mesh>
    <RoundedBox args={[5.4, 0.36, 3]} radius={0.6} smoothness={4} position={[0, 0.63, 0]} receiveShadow castShadow>
      <meshStandardMaterial color="#275d4b" roughness={0.55} metalness={0.12} />
    </RoundedBox>
    <RoundedBox args={[4.8, 0.04, 2.5]} radius={0.4} smoothness={4} position={[0, 0.84, 0]}>
      <meshStandardMaterial color="#ebdbc0" metalness={0.2} roughness={0.45} />
    </RoundedBox>
    {EXECUTIVES.map((agent) => <Person key={agent.id} agent={agent} selected={selected === agent.id}
      active={message?.sender === agent.id || message?.receiver === agent.id || statuses?.[agent.id]?.status === 'working'}
      onSelect={onSelect} />)}
    {message && <CommunicationBeam key={message.id} sender={message.sender} receiver={message.receiver} />}
    <OrbitControls enablePan={false} minPolarAngle={0.35} maxPolarAngle={1.3} minDistance={8} maxDistance={16} target={[0, 0.6, 0]} />
  </>
}

export default function Boardroom3D({ statuses = {}, events = [], onSelect, selected }) {
  const [reducedMotion, setReducedMotion] = useState(false)
  const [beam, setBeam] = useState(null)
  const [mode, setMode] = useState('3d')
  const lastSeen = useMemo(() => events?.[events.length - 1], [events])
  useEffect(() => {
    if (!lastSeen) return
    const sender = lastSeen.sender || lastSeen.source || lastSeen.data?.sender
    const receiver = lastSeen.receiver || lastSeen.data?.receiver
    const id = lastSeen.event_id
    if (!positionOf(sender) || !positionOf(receiver) || !id) return
    setBeam({ id, sender, receiver })
    const timeout = setTimeout(() => setBeam((current) => current?.id === id ? null : current), 2800)
    return () => clearTimeout(timeout)
  }, [lastSeen])
  useEffect(() => {
    const match = window.matchMedia('(prefers-reduced-motion: reduce)')
    const update = () => setReducedMotion(match.matches)
    update(); match.addEventListener?.('change', update)
    return () => match.removeEventListener?.('change', update)
  }, [])
  return <section className="boardroom-shell" aria-label="AI executive boardroom">
    <div className="boardroom-toolbar">
      <div><strong>Executive boardroom</strong><span>Five backend agents • Select an avatar to inspect its tasks</span></div>
      <button type="button" onClick={() => setMode(mode === '3d' ? 'list' : '3d')}>
        {mode === '3d' ? 'Accessible list view' : '3D view'}
      </button>
    </div>
    {mode === '3d' ? <div className="boardroom-canvas">
      <Canvas shadows={!reducedMotion} camera={{ position: [8, 8, 9], fov: 42 }} frameloop={reducedMotion ? 'demand' : 'always'}>
        <Suspense fallback={null}><Scene statuses={statuses} selected={selected} onSelect={onSelect} message={reducedMotion ? null : beam} /></Suspense>
      </Canvas>
    </div> : <div className="boardroom-list">
      {EXECUTIVES.map((agent) => <button key={agent.id} type="button" onClick={() => onSelect(agent.id)}>
        <span style={{ background: agent.color }} aria-hidden="true" />{agent.label} <small>{statuses?.[agent.id]?.status || 'Available'}</small>
      </button>)}
    </div>}
    <p className="boardroom-note">Communication trails appear only for backend events with a valid sender and receiver. No synthetic messages are generated.</p>
  </section>
}
