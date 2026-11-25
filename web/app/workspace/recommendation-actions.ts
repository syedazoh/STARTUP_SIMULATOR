"use server";
import {backend} from '../../lib/backend';
import type {Recommendation} from '../../lib/recommendations';
const base=(id:string)=>`/api/businesses/${encodeURIComponent(id)}/recommendations`;
export async function readRecommendations(id:string){try{return {ok:true as const,data:await backend(base(id)) as Recommendation[]}}catch(error){return {ok:false as const,error:error instanceof Error?error.message:'Recommendations unavailable.'}}}
export async function recommendationCommand(id:string,command:'create'|'decision'|'revise',payload:Record<string,unknown>,planId=''){try{const path=base(id)+(command==='create'?'':`/${encodeURIComponent(planId)}${command==='decision'?'/decision':''}`);return {ok:true as const,data:await backend(path,{method:command==='revise'?'PUT':'POST',body:JSON.stringify(payload),signal:AbortSignal.timeout(90000)}) as Recommendation}}catch(error){return {ok:false as const,error:error instanceof Error?error.message:'Recommendation could not finish. Refresh before retrying.'}}}
