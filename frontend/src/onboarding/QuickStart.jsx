'use client';
import { useRef } from 'react';
export default function QuickStart({classic=false}) {
 const video=useRef(null);
 return <section className="quick-start" aria-labelledby="quick-start-title">
  <h2 id="quick-start-title">Your first plan, step by step.</h2>
  <p>Watch the captioned product demo, then follow the checklist below. The recording uses synthetic data and performs no real-world actions.</p>
  {classic&&<p>The recording shows the executive workspace. In this classic interface, use Company setup, Command Center, the agent workspaces and Decision History for the same review cycle.</p>}
  <details onToggle={event=>{if(!event.currentTarget.open)video.current?.pause()}}>
   <summary>Watch the product demo</summary>
   <video ref={video} controls playsInline preload="none" poster="/media/quick-start-poster.jpg" aria-label="Startup Simulator quick-start demo">
    <source src="/media/quick-start.mp4" type="video/mp4"/>
    <track kind="captions" src="/media/quick-start.vtt" srcLang="en" label="English" default/>
    Your browser cannot play this video. Follow the transcript below or <a href="/media/quick-start.mp4">download the demo</a>.
   </video>
   <p>Captioned, audio-free screen recording · executive workspace · synthetic demonstration. Use the player to pause, seek or enter full screen. On a phone, use full screen for the clearest view.</p>
  </details>
  <ol>
   <li><strong>Create your company.</strong> Add its name, industry and simulated starting resources. Complete the business profile so departments have context.</li>
   <li><strong>Set a clear goal.</strong> Describe the outcome, budget and constraints. In the executive workspace, ask the CEO for a plan; inspect its assignments before activating them. In the classic workspace, begin with the relevant agent’s proposal controls.</li>
   <li><strong>Review the proposed work.</strong> Check the department, exact payload, cost and simulation/live mode. CEO review and your owner approval are different steps.</li>
   <li><strong>Approve only what you understand.</strong> Approval can execute an eligible action. Request changes or reject it when the details are wrong. A visual preview never approves work.</li>
   <li><strong>Follow the boardroom.</strong> Recorded handoffs show who sends and receives work. Select a department to inspect it; All events restores the full team.</li>
   <li><strong>Check the outcome.</strong> Read task status, decision history and available reports. Executed, delivered and verified complete are different claims. Connect external accounts only when their integration is ready.</li>
  </ol>
  <details><summary>Read the video transcript</summary><p>Start by creating a business and entering your simulator starting values. Give the CEO a concrete goal and review the resulting assignments. Activate the plan only after inspecting it. Open the executive studio to see recorded work. Expand an exact action before approving it. Approval may execute that action, so check its mode and payload first. Watch the recorded handoff and refreshed task result, then return to the command center for history and reports. This demonstration uses a disposable local identity, synthetic tasks and a simulated result. It does not prove live email delivery, social publication or deployment.</p></details>
  {!classic&&<section id="classic-interface"><h3>Where are the original agent tools?</h3><p>This repository has two interfaces sharing one backend. The executive interface uses Supabase sign-in. Original publishing, media and connected-account screens remain in the classic interface, which uses your original Startup Simulator login.</p><p>For local development, keep FastAPI and the original Mongo database running, then start the classic frontend in another terminal:</p><pre>cd frontend<br/>npm ci<br/>npm run dev</pre><a href="http://localhost:5173" target="_blank" rel="noreferrer">Open the local classic interface (port 5173)</a><p>Select the same company and open its agent pages. Do not create a new Supabase project or company to recover old work. If a company is missing, check the original MongoDB database and use Link existing account in the executive workspace.</p></section>}
 </section>;
}
