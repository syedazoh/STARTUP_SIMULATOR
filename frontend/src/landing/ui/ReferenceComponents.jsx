'use client';
// Adapted from Skiper legacy ExpandedTabs (MIT, Jordan-Gilliam) and
// Vengence UI staggerText (MIT, Ashutoshx7). See THIRD_PARTY_NOTICES.md.
// App-owned motion primitives preserve the React 18/19 and Docker boundaries.
export function ExpandedAgentTabs({agents,index,onChange,enabled,animation}) {
 const Button=animation.button,Span=animation.span,Presence=animation.Presence;
 return <div className="launch-chapter-tabs" aria-label="Agent chapters">{agents.map((agent,i)=><Button key={agent.id} type="button" initial={false} animate={{backgroundColor:index===i?'var(--launch-soft)':'transparent'}} transition={{duration:enabled?.25:0}} aria-label={`Explore ${agent.name} chapter`} aria-pressed={index===i} onClick={()=>onChange(i)}><span className="launch-chapter-dot" style={{background:agent.color}}/>{agent.name}<Presence initial={false}>{index===i&&<Span className="launch-chapter-role" initial={enabled?{width:0,opacity:0}:false} animate={{width:'auto',opacity:1}} exit={{width:0,opacity:0}} transition={{duration:enabled?.3:0,ease:[.22,1,.36,1]}}>{agent.role}</Span>}</Presence></Button>)}</div>;
}
export function StaggerText({text,enabled,animation}) {
 const Span=animation.span;
 return <span className="launch-stagger"><span className="launch-sr-only">{text}</span><Span aria-hidden="true" initial={false} whileInView={enabled?'show':'still'} viewport={{once:true}} variants={{show:{transition:{staggerChildren:.055}},still:{transition:{duration:0}}}}>{text.split(' ').map((word,i)=><span className="launch-word" key={`${word}-${i}`}><Span variants={{show:{y:[12,0],opacity:[.65,1],transition:{duration:.6,ease:[.22,1,.36,1]}},still:{y:0,opacity:1,transition:{duration:0}}}}>{word}</Span>{' '}</span>)}</Span></span>;
}
