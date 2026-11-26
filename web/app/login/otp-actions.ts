"use server";
export async function requestEmailCode(_email:string){return {ok:false as const,error:'Email-code sign-in is disabled. Use your original email and password.'}}
export async function verifyEmailCode(_email:string,_code:string,_next:string){return {ok:false as const,error:'Email-code sign-in is disabled. Use your original email and password.'}}
export async function cancelEmailCode(){}
