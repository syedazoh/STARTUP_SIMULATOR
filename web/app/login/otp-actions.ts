"use server";
import {cookies} from 'next/headers';
import {redirect} from 'next/navigation';
import {supabase} from '../../lib/supabase';
import {backend} from '../../lib/backend';
import {authConfigurationIssue} from '../../lib/auth-state';
import {validEmail,safeReturnTo,otpNotice} from '../../lib/login-flow';
const pending='startup-pending-email';
export async function requestEmailCode(email:string){
 if(!validEmail(email))return {ok:false as const,error:'Enter a valid email address.'};
 if(authConfigurationIssue(process.env))return {ok:false as const,error:'Configure the existing Supabase project in web/.env.local, then restart Next.js.'};
 try{const client=await supabase();const {error}=await client.auth.signInWithOtp({email:email.trim().toLowerCase(),options:{shouldCreateUser:false}});if(error)return {ok:false as const,error:error.status===429?otpNotice(error):'Could not request a code. Check the email provider settings, retry shortly, or use your Supabase password.'};
 (await cookies()).set(pending,email.trim().toLowerCase(),{httpOnly:true,sameSite:'lax',secure:process.env.NODE_ENV==='production',path:'/login',maxAge:600});return {ok:true as const};
 }catch{return {ok:false as const,error:'Cannot reach the authentication provider. Check its configuration and network.'}}
}
export async function verifyEmailCode(email:string,code:string,next:string){
 if(!validEmail(email)||typeof code!=='string'||!/^\d{6,10}$/.test(code))return {ok:false as const,error:'Enter the code from the latest email.'};
 try{const client=await supabase();const result=await client.auth.verifyOtp({email:email.trim().toLowerCase(),token:code,type:'email'});if(result.error||!result.data.session)return {ok:false as const,error:otpNotice(result.error)};(await cookies()).set(pending,'',{path:'/login',maxAge:0,httpOnly:true,sameSite:'lax',secure:process.env.NODE_ENV==='production'});
 }catch{return {ok:false as const,error:'Verification could not finish. Retry or request a fresh code.'}}
 let target=safeReturnTo(next);
 if(target==='/workspace'){try{const businesses=await backend('/api/businesses');if(Array.isArray(businesses)&&businesses.length===1)target=`/workspace/${encodeURIComponent(businesses[0].id)}`}catch{/* The selector explains backend/ownership linking failures without creating a replacement company. */}}
 redirect(target);
}

export async function cancelEmailCode(){(await cookies()).set(pending,'',{path:'/login',maxAge:0,httpOnly:true,sameSite:'lax',secure:process.env.NODE_ENV==='production'})}
