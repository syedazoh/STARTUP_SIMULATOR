"use client";
import AgentWorkflow from './agent-workflow';
export default function AgentConversation({businessId,role}:{businessId:string;role:string}){return <AgentWorkflow businessId={businessId} role={role} boardroom/>}
