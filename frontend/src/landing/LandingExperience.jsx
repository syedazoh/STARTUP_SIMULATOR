'use client';
import { useEffect, useRef, useState } from 'react';
import LaunchWalkthrough from './LaunchWalkthrough';
import {ExpandedAgentTabs,StaggerText} from './ui/ReferenceComponents';
import { INTRODUCTIONS, nextIntroduction, initialTheme } from './agents.mjs';

function Symbol({name, ...props}) {
 const paths={play:'m9 5 11 7-11 7Z',pause:'M8 5v14M16 5v14',arrow:'M5 12h14m-6-6 6 6-6 6',back:'M19 12H5m6-6-6 6 6 6',sun:'M12 3v2m0 14v2M3 12h2m14 0h2M5.6 5.6 7 7m10 10 1.4 1.4M5.6 18.4 7 17M17 7l1.4-1.4M16 12a4 4 0 1 1-8 0 4 4 0 0 1 8 0',moon:'M20 15A9 9 0 0 1 9 4a9 9 0 1 0 11 11Z',sound:'m4 9 4 0 5-4v14l-5-4H4ZM17 8q5 4 0 8',muted:'m4 9 4 0 5-4v14l-5-4H4ZM17 9l5 6m0-6-5 6',close:'m6 6 12 12M6 18 18 6',cube:'m12 2 9 5v10l-9 5-9-5V7Zm0 10 9-5M12 12 3 7m9 5v10',expand:'M4 9V4h5m6 0h5v5m0 6v5h-5M9 20H4v-5',check:'m5 12 4 4L19 6'};
 return <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}><path d={paths[name]||paths.arrow}/></svg>;
}
export default function LandingExperience({signupHref='/signup',loginHref='/login',loadThree,animation}) {
 const [theme,setTheme]=useState('dark'),[index,setIndex]=useState(0),[focused,setFocused]=useState(false),[tour,setTour]=useState(false),[audio,setAudio]=useState(true),[voiceStatus,setVoiceStatus]=useState(''),[sceneState,setSceneState]=useState('loading');
 const [motionEnabled,setMotionEnabled]=useState(true),[systemReduced,setSystemReduced]=useState(false);
 const motion=motionEnabled&&!systemReduced;
 const canvas=useRef(null),engine=useRef(null),dialog=useRef(null),manualTheme=useRef(false),observer=useRef(null);
 const current=useRef({theme,index,focused,motion});current.current={theme,index,focused,motion};
 const agent=INTRODUCTIONS[index];
 useEffect(()=>{
  const preference=matchMedia('(prefers-reduced-motion: reduce)');
  try{setMotionEnabled(localStorage.getItem('startup-landing-motion')!=='off')}catch{/* Motion remains usable without storage. */}
  setSystemReduced(preference.matches);
  const update=()=>setSystemReduced(preference.matches);preference.addEventListener('change',update);
  return()=>preference.removeEventListener('change',update);
 },[]);
 useEffect(()=>{engine.current?.setReducedMotion(!motion);if(!motion)setTour(false)},[motion]);
 useEffect(()=>{
  const preference=matchMedia('(prefers-color-scheme: dark)');let stored=null;
  try{stored=localStorage.getItem('startup-landing-theme')}catch{/* Private browsing can disable storage. */}
  manualTheme.current=stored==='light'||stored==='dark';setTheme(initialTheme(stored,preference.matches));
  const update=()=>{if(!manualTheme.current)setTheme(preference.matches?'dark':'light')};preference.addEventListener('change',update);
  return()=>preference.removeEventListener('change',update);
 },[]);
 useEffect(()=>{
  let disposed=false;
  Promise.all([loadThree(),import('../studio/scene.mjs')]).then(([THREE,{createStudio}])=>{
   if(disposed||!canvas.current)return;
   engine.current=createStudio(THREE,canvas.current,{reducedMotion:!current.current.motion,onSelect:id=>{const i=INTRODUCTIONS.findIndex(a=>a.id===id);if(i>=0){setIndex(i);setFocused(true)}}});
   engine.current.setTheme(current.current.theme);engine.current.select(INTRODUCTIONS[current.current.index].id);engine.current.showOnly(current.current.focused?INTRODUCTIONS[current.current.index].id:null);observer.current=new IntersectionObserver(entries=>engine.current?.setVisible(entries[0].isIntersecting));observer.current.observe(canvas.current);setSceneState('ready');
  }).catch(()=>{if(!disposed)setSceneState('unavailable')});
  const node=canvas.current;const lost=e=>{e.preventDefault();setSceneState('unavailable')};node?.addEventListener('webglcontextlost',lost);
  return()=>{disposed=true;observer.current?.disconnect();node?.removeEventListener('webglcontextlost',lost);engine.current?.dispose();engine.current=null};
 },[loadThree]);
 useEffect(()=>{
  const root=document.documentElement;const oldScheme=root.style.colorScheme;root.style.colorScheme=theme;
  let meta=document.querySelector('meta[name="theme-color"]');const created=!meta;const oldColor=meta?.getAttribute('content');
  if(!meta){meta=document.createElement('meta');meta.setAttribute('name','theme-color');document.head.append(meta)}
  meta.setAttribute('content',theme==='dark'?'#0d0a13':'#f4f0e9');
  return()=>{root.style.colorScheme=oldScheme;if(created)meta.remove();else if(oldColor!==null)meta.setAttribute('content',oldColor)};
 },[theme]);
 useEffect(()=>{engine.current?.setTheme(theme)},[theme]);
 useEffect(()=>{engine.current?.select(agent.id);engine.current?.showOnly(focused?agent.id:null)},[agent.id,focused]);
 useEffect(()=>{
  if(!tour)return;
  let active=true,timer;const synth=window.speechSynthesis;
  const advance=()=>{if(!active)return;if(!motion||index===INTRODUCTIONS.length-1){setTour(false);setVoiceStatus(motion?'Tour complete. Explore any executive.':'Introduction complete. Choose another executive.')}else setIndex(i=>i+1)};
  const fallback=()=>{clearTimeout(timer);if(active){setVoiceStatus(audio?'Voice unavailable here. Follow the captions.':'Captions only');timer=setTimeout(advance,16000)}};
  if(audio&&synth&&window.SpeechSynthesisUtterance){
   const utterance=new SpeechSynthesisUtterance(agent.speech);utterance.lang='en-US';utterance.rate=.95;utterance.onstart=()=>{if(active)setVoiceStatus('Speaking · English')};utterance.onend=advance;utterance.onerror=fallback;synth.cancel();setVoiceStatus('Preparing English voice…');synth.speak(utterance);
   // Some devices expose speech synthesis but never start it.
   timer=setTimeout(()=>{if(active&&!synth.speaking){synth.cancel();fallback()}},3500);
  }else fallback();
  return()=>{active=false;clearTimeout(timer);synth?.cancel()};
 },[tour,index,audio,agent.speech,motion]);
 useEffect(()=>{
  const stop=()=>{if(document.hidden){setTour(false);window.speechSynthesis?.cancel()}};document.addEventListener('visibilitychange',stop);window.addEventListener('pagehide',stop);
  return()=>{document.removeEventListener('visibilitychange',stop);window.removeEventListener('pagehide',stop);window.speechSynthesis?.cancel()};
 },[]);
 function toggleTheme(){const value=theme==='dark'?'light':'dark';manualTheme.current=true;setTheme(value);try{localStorage.setItem('startup-landing-theme',value)}catch{/* Theme still works without storage. */}}
 function toggleMotion(){const value=!motionEnabled;setMotionEnabled(value);try{localStorage.setItem('startup-landing-motion',value?'on':'off')}catch{/* Motion still works without storage. */}}
 function choose(i){setIndex(i);setFocused(true)}
 function start(){setIndex(0);setFocused(true);setTour(true);document.getElementById('executives')?.scrollIntoView({block:'center',behavior:motion?'smooth':'instant'})}
 return <main className="launch-page" data-theme={theme} data-motion={motion?'on':'off'}>
  <a className="launch-skip" href="#launch-title">Skip to content</a>
  <div className="launch-atmosphere" aria-hidden="true"><div/><div/></div>
  <header className="launch-nav launch-glass">
   <a className="launch-brand" href="/" aria-label="Startup Simulator home"><span><Symbol name="cube"/></span><strong>Startup<span>simulator</span></strong></a>
   <nav aria-label="Landing navigation"><a href="#executives">The team</a><a href="#launch-walkthrough">How it works</a><a href="#plans">Plans</a></nav>
   <div className="launch-nav-actions"><button className="launch-motion" aria-pressed={motion} disabled={systemReduced} title={systemReduced?'Reduced motion follows your device setting':'Toggle page motion'} onClick={toggleMotion}><Symbol name={motion?'pause':'play'}/><span>Motion {motion?'on':'off'}</span></button><button className="launch-icon" onClick={toggleTheme} aria-label={`Switch to ${theme==='dark'?'light':'dark'} mode`}><Symbol name={theme==='dark'?'sun':'moon'}/></button><a className="launch-signin" href={loginHref}>Sign in <Symbol name="arrow"/></a></div>
  </header>
  <section className="launch-hero" aria-labelledby="launch-title">
   <div className="launch-hero-copy"><h1 id="launch-title" tabIndex={-1}><StaggerText text="Your idea." enabled={motion} animation={animation}/>{' '}<br/>A team to<br/><em>move it forward.</em></h1><p>Give your startup a direction. Watch five AI departments plan together, bring proposals to the table, and put the next decision in your hands.</p>
    <div className="launch-actions"><a className="launch-primary" href="#demo">Explore the free demo <Symbol name="arrow"/></a><button className="launch-secondary" onClick={start}><Symbol name="play"/> Meet the team</button></div>
    <p className="launch-promise"><Symbol name="check"/> Simulate the possibilities. You make the call.</p>
   </div>
   <section className="launch-stage launch-glass" aria-label="Interactive executive showcase" id="executives">
    <div className="launch-stage-top"><span><i/> {tour?'Guided introduction':'Executive floor'}</span><button className="launch-small" onClick={()=>{setFocused(!focused);setTour(false)}}>{focused?'Show full team':'Spotlight agent'}<Symbol name="expand"/></button></div>
    <div className="launch-canvas"><canvas ref={canvas} aria-label="Interactive 3D executives. Drag to orbit or choose an agent below."/>{sceneState!=='ready'&&<div className="launch-scene-status" role="status">{sceneState==='loading'?'Preparing your executive team…':'3D is unavailable on this device. Meet every agent using the controls below.'}</div>}<span className="launch-scene-note">Interactive 3D · illustrative preview</span></div>
    <div className="launch-agent-tabs" aria-label="Choose an executive">{INTRODUCTIONS.map((a,i)=><button key={a.id} aria-pressed={index===i} onClick={()=>choose(i)}><i style={{background:a.color}}/>{a.name}</button>)}</div>
   </section>
  </section>
  <div className="launch-manifesto"><span>One idea. Five perspectives.</span><p>From the first proposal to the final decision.</p><a href="#demo">See it in action <Symbol name="arrow"/></a></div>
  <section className="launch-chapters" aria-labelledby="launch-chapters-title"><div><h2 id="launch-chapters-title">Five perspectives.<br/>One shared ambition.</h2><p>Choose a department. Get to know its role, then hear how it fits into your company.</p></div><ExpandedAgentTabs agents={INTRODUCTIONS} index={index} onChange={choose} enabled={motion} animation={animation}/></section>
  <section className="launch-introduction launch-glass" aria-label="Agent introduction">
   <div className="launch-intro-heading"><span className="launch-agent-number">{String(index+1).padStart(2,'0')}<span> / 05</span></span><div><p>{agent.name}</p><span>{agent.role}</span></div></div>
   <animation.div className="launch-profile" key={agent.id} initial={motion?{opacity:.65,x:14}:false} animate={{opacity:1,x:0}} transition={{duration:motion?.32:0,ease:[.22,1,.36,1]}}><h2>{agent.title}</h2><p>{agent.description}</p><span className="launch-example"><Symbol name="arrow"/>{agent.example}</span></animation.div>
   <div className="launch-player"><div className="launch-player-controls"><button className="launch-icon" aria-label="Previous agent" onClick={()=>choose(nextIntroduction(index,-1))}><Symbol name="back"/></button><button className="launch-play" aria-label={tour?'Pause introduction':'Play introduction'} aria-pressed={tour} onClick={()=>{setFocused(true);setTour(!tour)}}><Symbol name={tour?'pause':'play'}/></button><button className="launch-icon" aria-label="Next agent" onClick={()=>choose(nextIntroduction(index))}><Symbol name="arrow"/></button><button className="launch-icon" aria-label={audio?'Mute narration':'Enable narration'} aria-pressed={audio} onClick={()=>setAudio(!audio)}><Symbol name={audio?'sound':'muted'}/></button></div><p role="status">{tour||voiceStatus.includes('complete.')?voiceStatus:'English narration · tap play'}</p><details className="launch-caption"><summary>Read the narration</summary><p>{agent.speech}</p></details></div>
  </section>
  {tour&&<div className="launch-live-caption launch-glass" role="status"><strong>{agent.name}</strong><p>{agent.speech}</p><button className="launch-icon" aria-label="Close captions and pause tour" onClick={()=>setTour(false)}><Symbol name="close"/></button></div>}
  <section className="launch-process" id="process"><div><h2>Give the idea a direction.<br/>Keep the decisions yours.</h2><p>The boardroom makes business decisions visible. Watch proposals move between departments, inspect the reasoning and review the actions that need your approval.</p><button className="launch-secondary" onClick={()=>dialog.current?.showModal()}>See how it works <Symbol name="arrow"/></button></div><ol className="launch-steps launch-glass"><li><span>01</span><div><h3>Set the scene</h3><p>Create your company and describe the goals.</p></div></li><li><span>02</span><div><h3>Bring the team together</h3><p>Explore proposals, requests and recorded handoffs.</p></div></li><li><span>03</span><div><h3>Make the call</h3><p>Review the exact action, then approve or request changes.</p></div></li><li><span>04</span><div><h3>Learn from the result</h3><p>Follow simulation outcomes and decision history.</p></div></li></ol></section>
  <LaunchWalkthrough loadThree={loadThree} theme={theme} enabled={motion} animation={animation}/>
  <section className="launch-demo" id="demo" aria-labelledby="launch-demo-title">
   <div className="launch-demo-copy"><h2 id="launch-demo-title">Your first move,<br/><em>without the guesswork.</em></h2><p>See how a goal becomes a plan, how departments coordinate, and where your approval fits. Start with a walkthrough using synthetic business data.</p><ul><li><Symbol name="check"/> Follow proposals and department handoffs</li><li><Symbol name="check"/> Understand the owner approval step</li><li><Symbol name="check"/> Review a simulated result</li></ul><a className="launch-primary" href="/getting-started">Watch the demo &amp; quick start <Symbol name="arrow"/></a><p className="launch-demo-note">The walkthrough is public. Create an account to run a business-scoped simulation.</p></div>
   <a className="launch-film launch-glass" href="/getting-started" aria-label="Open the captioned project demo"><img src="/media/quick-start-poster.jpg" alt="Startup Simulator executive workspace shown in the synthetic demo recording" width="1440" height="900" loading="lazy"/><span className="launch-film-play"><Symbol name="play"/></span><span className="launch-film-caption"><strong>See the decision take shape.</strong><span>Captioned recording · synthetic demonstration <Symbol name="arrow"/></span></span></a>
  </section>
  <section className="launch-plans" id="plans" aria-labelledby="launch-plans-title"><div className="launch-plans-heading"><h2 id="launch-plans-title">Start with a simulation.<br/>Find your next step.</h2><p>Explore the workflow before deciding what your startup needs.</p></div><div className="launch-plan-grid"><article className="launch-free launch-glass"><div className="launch-plan-title"><h3>Free</h3><span>Demo simulation</span></div><p>Meet the team. Explore the walkthrough. Create a company to try the synthetic launch workflow.</p><a className="launch-primary" href={signupHref}>Create your free demo account <Symbol name="arrow"/></a><p className="launch-demo-note">Synthetic outcomes. No real emails, posts or spending from the demo.</p></article><article className="launch-future"><h3>What comes next</h3><p>Further plans are being defined. Features, limits and pricing will be shared when they are ready.</p><span className="launch-planned">Planned</span></article></div></section>
  <section className="launch-close launch-glass"><h2>There’s a team<br/>behind your next move.</h2><a className="launch-primary" href={signupHref}>Take your seat <Symbol name="arrow"/></a><p>This page is an illustrative introduction. Sign in to see your business’s recorded work.</p></section>
  <footer className="launch-footer"><a href="/">Startup Simulator</a><span>Five departments. One shared direction.</span><a href={loginHref}>Already have a company? Sign in</a></footer>
  <dialog className="launch-dialog launch-glass" ref={dialog} aria-labelledby="launch-dialog-title"><button className="launch-icon launch-dialog-close" aria-label="Close overview" onClick={()=>dialog.current?.close()}><Symbol name="close"/></button><h2 id="launch-dialog-title">A clear path from idea to decision.</h2><p>The CEO coordinates the team. Finance reviews resources, Marketing proposes campaigns, HR evaluates staffing, and Operations plans capacity.</p><p>In your workspace, the boardroom shows recorded tasks and communication. You inspect actions requiring approval before the backend executes them.</p><p>The landing tour is a visual introduction. It creates no tasks, sends no messages and spends no money.</p><a className="launch-primary" href={signupHref}>Create your startup <Symbol name="arrow"/></a></dialog>
 </main>;
}
