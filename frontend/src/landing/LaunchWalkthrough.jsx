'use client';
import {useEffect,useRef,useState} from 'react';
import {LAUNCH_STEPS,nextLaunchStep,participantName} from './launch-scenario.mjs';
export default function LaunchWalkthrough({loadThree,theme,enabled,animation}) {
 const [index,setIndex]=useState(0),[playing,setPlaying]=useState(false),[visible,setVisible]=useState(false),[sceneState,setSceneState]=useState('loading');
 const section=useRef(null),canvas=useRef(null),engine=useRef(null),latest=useRef(null);
 const step=LAUNCH_STEPS[index];latest.current={step,theme,enabled};
 const Div=animation.div;
 useEffect(()=>{
  let disposed=false;
  const observer=new IntersectionObserver(([entry])=>{setVisible(entry.isIntersecting);engine.current?.setVisible(entry.isIntersecting)},{threshold:.1});observer.observe(section.current);
  Promise.all([loadThree(),import('../studio/scene.mjs')]).then(([THREE,{createStudio}])=>{
   if(disposed||!canvas.current)return;
   const state=latest.current;engine.current=createStudio(THREE,canvas.current,{reducedMotion:!state.enabled});
   engine.current.setTheme(state.theme);engine.current.playTransfer({...state.step,source:'synthetic landing walkthrough'});setSceneState('ready');
  }).catch(()=>{if(!disposed)setSceneState('unavailable')});
  const node=canvas.current;const lost=e=>{e.preventDefault();setSceneState('unavailable');setPlaying(false)};node?.addEventListener('webglcontextlost',lost);
  return()=>{disposed=true;observer.disconnect();node?.removeEventListener('webglcontextlost',lost);engine.current?.dispose();engine.current=null};
 },[loadThree]);
 useEffect(()=>{engine.current?.setVisible(visible)},[visible,sceneState]);
 useEffect(()=>{engine.current?.setTheme(theme)},[theme]);
 useEffect(()=>{engine.current?.setReducedMotion(!enabled);if(!enabled)setPlaying(false)},[enabled]);
 useEffect(()=>{engine.current?.showOnly(null);engine.current?.select(step.receiver==='owner'?'ceo':step.receiver);engine.current?.playTransfer({...step,source:'synthetic landing walkthrough'})},[step]);
 useEffect(()=>{if(!playing||!enabled||!visible)return;const timer=setTimeout(()=>{if(index===LAUNCH_STEPS.length-1)setPlaying(false);else setIndex(i=>nextLaunchStep(i))},5200);return()=>clearTimeout(timer)},[playing,enabled,visible,index]);
 useEffect(()=>{const pause=()=>{if(document.hidden)setPlaying(false)};document.addEventListener('visibilitychange',pause);return()=>document.removeEventListener('visibilitychange',pause)},[]);
 function choose(i){setPlaying(false);if(i===index)engine.current?.playTransfer({...step,source:'synthetic landing walkthrough'});setIndex(i)}
 function togglePlayback(){if(!playing){if(index===LAUNCH_STEPS.length-1)setIndex(0);else engine.current?.playTransfer({...step,source:'synthetic landing walkthrough'})}setPlaying(!playing)}
 return <section className="launch-walkthrough" ref={section} id="launch-walkthrough" aria-labelledby="walkthrough-title">
  <div className="launch-walkthrough-heading"><h2 id="walkthrough-title">One launch.<br/><em>Every handoff, visible.</em></h2><p>Follow a fictional product launch through the boardroom. This is an interactive explanation using synthetic data, separate from your business’s recorded work.</p></div>
  <div className="launch-meeting launch-glass"><div className="launch-meeting-scene"><div className="launch-meeting-top"><span>Synthetic walkthrough</span><span>Step {index+1} of {LAUNCH_STEPS.length}</span></div><canvas ref={canvas} aria-label="Synthetic launch boardroom with directional handoff lines. Every step is also explained in text."/>{sceneState!=='ready'&&<p className="launch-meeting-fallback" role="status">{sceneState==='loading'?'Preparing the launch walkthrough…':'3D is unavailable. Follow every handoff in the steps and route below.'}</p>}<div className="launch-meeting-route" aria-live="polite"><strong>{participantName(step.sender)} <span aria-label="to">→</span> {participantName(step.receiver)}</strong><span>{step.label} · illustrative</span></div></div>
   <div className="launch-meeting-details"><Div key={step.id} initial={enabled?{opacity:.65,x:12}:false} animate={{opacity:1,x:0}} transition={{duration:enabled?.3:0,ease:[.22,1,.36,1]}}><h3>{step.title}</h3><p>{step.detail}</p><dl><dt>What moves between them</dt><dd>{step.artifact}</dd></dl></Div><div className="launch-meeting-controls"><button className="launch-icon" aria-label="Previous walkthrough step" disabled={index===0} onClick={()=>choose(nextLaunchStep(index,-1))}><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true"><path d="M19 12H5m6-6-6 6 6 6"/></svg></button><button className="launch-secondary" disabled={!enabled} aria-pressed={playing} onClick={togglePlayback}>{playing?'Pause walkthrough':'Play walkthrough'}</button><button className="launch-icon" aria-label="Next walkthrough step" disabled={index===LAUNCH_STEPS.length-1} onClick={()=>choose(nextLaunchStep(index))}><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true"><path d="M5 12h14m-6-6 6 6-6 6"/></svg></button></div>{!enabled&&<p className="launch-motion-note">Motion is off. Choose any step to explore at your own pace.</p>}</div>
  </div>
  <ol className="launch-handoff-steps" aria-label="Launch handoff steps">{LAUNCH_STEPS.map((item,i)=><li key={item.id}><button aria-current={i===index?'step':undefined} onClick={()=>choose(i)}><span>{String(i+1).padStart(2,'0')}</span><strong>{item.label}</strong><span>{participantName(item.sender)} → {participantName(item.receiver)}</span></button></li>)}</ol>
 </section>;
}
