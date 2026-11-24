'use client';
import {useEffect,useRef,useState} from 'react';
// Shared procedural avatar: illustration of the selected role, never proof of work.
export default function AgentAvatar({agent,loadThree,caption='Department avatar'}) {
 const canvas=useRef(null),engine=useRef(null);const [sceneState,setSceneState]=useState('loading');
 useEffect(()=>{
  setSceneState('loading');let disposed=false;const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  const update=()=>engine.current?.setReducedMotion(reduced.matches);let observer;
  Promise.all([loadThree(),import('./scene.mjs')]).then(([THREE,{createStudio}])=>{
   if(disposed)return;engine.current=createStudio(THREE,canvas.current,{reducedMotion:reduced.matches});engine.current.showOnly(agent);engine.current.select(agent);setSceneState('ready');
   observer=new IntersectionObserver(([entry])=>engine.current?.setVisible(entry.isIntersecting));observer.observe(canvas.current);
  }).catch(()=>{if(!disposed)setSceneState('unavailable')});
  reduced.addEventListener('change',update);
  return()=>{disposed=true;reduced.removeEventListener('change',update);observer?.disconnect();engine.current?.dispose();engine.current=null};
 },[agent,loadThree]);
 return <figure className="agent-presence" data-scene={sceneState}><canvas ref={canvas} aria-label={`${agent} department avatar`}/>{sceneState!=='ready'&&<span className="agent-presence-fallback">{agent.toUpperCase()}</span>}<figcaption>{caption}</figcaption></figure>;
}
