"use server";
import {backend} from '../../../../../lib/backend';
import {agentRole,settingsPayload,chatPayload} from '../../../../../lib/agent-tools-contracts';
export type Mode={mode:'manual'|'auto';auto_thresholds:{auto_approve_max:number|null}};
export type Policy={enabled:boolean;auto_approve_max:number|null;auto_deny_min:number|null};
export type Message={role:string;content:string;created_at:string;answer_source?:string;intent?:string};
export type Thread={messages:Message[]};
type Result<T>={data:T|null;error?:string};
export type ToolsData={mode:Result<Mode>;policy:Result<Policy>;chat:Result<Thread>;history:Result<{state:Record<string,unknown>}[]>};
const root=(businessId:string,role:string)=>`/api/businesses/${encodeURIComponent(businessId)}/agents/${agentRole(role)}`;
async function read<T>(path:string):Promise<Result<T>>{try{return {data:await backend(path)}}catch(error){return {data:null,error:error instanceof Error?error.message:'Section unavailable'}}}
export async function readAgentTools(businessId:string,role:string):Promise<ToolsData>{const path=root(businessId,role);const [chat,history,mode,policy]=await Promise.all([role==='strategy'?Promise.resolve({data:null}):read<Thread>(path+'/chat'),read<{state:Record<string,unknown>}[]>(path+'/history?limit=50'),['ceo','strategy'].includes(role)?Promise.resolve({data:null}):read<Mode>(path+'/mode'),['ceo','strategy'].includes(role)?Promise.resolve({data:null}):read<Policy>(path+'/policy')]);return {chat,history,mode,policy}}
export async function saveAgentSettings(businessId:string,role:string,kind:string,form:FormData){try{const payload=settingsPayload(role,kind,form);await backend(root(businessId,role)+'/'+kind,{method:'PUT',body:JSON.stringify(payload)});return {ok:true as const,data:await readAgentTools(businessId,role)}}catch(error){return {ok:false as const,error:error instanceof Error?error.message:'Settings could not be saved.'}}}
export async function sendAgentMessage(businessId:string,role:string,content:string,screen:'agent_workspace'|'boardroom'='agent_workspace'){try{const result=await backend(root(businessId,role)+'/chat',{method:'POST',body:JSON.stringify({...chatPayload(content),screen_context:{screen:screen==='boardroom'?'boardroom':'agent_workspace'}}),signal:AbortSignal.timeout(90000)}) as {thread:Thread;ai_error?:string;task?:{id:string;status:string}};return {ok:true as const,...result}}catch(error){return {ok:false as const,error:error instanceof Error?error.message:'Message could not be sent.'}}}

export async function readAgentConversation(businessId:string,role:string){return read<Thread>(root(businessId,role)+'/chat')}
