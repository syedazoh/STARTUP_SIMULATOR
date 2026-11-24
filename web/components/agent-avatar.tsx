"use client";
import AgentAvatar from '../../frontend/src/studio/AgentAvatar';
const loadThree=()=>import('three');
export default function Avatar({agent,caption}:{agent:string;caption?:string}){return <AgentAvatar agent={agent} caption={caption} loadThree={loadThree}/>}
