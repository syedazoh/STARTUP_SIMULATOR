"use server";
import {cookies} from 'next/headers';
import {redirect} from 'next/navigation';
import {safeReturnTo,validEmail} from '../lib/login-flow';
import {ACCESS_COOKIE,backendUrl,accessOptions,refreshedCookie} from '../lib/native-session';
import {logoutSessions} from '../lib/logout-sessions';
function fields(form:FormData,page:string,next:string){const email=String(form.get('email')||'').trim().toLowerCase(),password=String(form.get('password')||'');if(!validEmail(email)||password.length<8||password.length>128)redirect(`${page}?error=input&next=${encodeURIComponent(next)}`);return {email,password}}
export async function login(form:FormData){
 const next=safeReturnTo(form.get('next')),credentials=fields(form,'/login',next);let response:Response;
 try{response=await fetch(`${backendUrl()}/api/auth/login`,{method:'POST',headers:{'Content-Type':'application/json','X-Requested-With':'XMLHttpRequest'},body:JSON.stringify(credentials),cache:'no-store',signal:AbortSignal.timeout(12000)})}catch{redirect(`/login?error=unavailable&next=${encodeURIComponent(next)}`)}
 if(!response.ok)redirect(`/login?error=${response.status===429?'rate':response.status>=500?'unavailable':'login'}&next=${encodeURIComponent(next)}`);
 const data=await response.json().catch(()=>null),refresh=refreshedCookie(response);if(!data||typeof data.access_token!=='string'||!refresh)redirect('/login?error=unavailable');
 const jar=await cookies();jar.set(ACCESS_COOKIE,data.access_token,accessOptions());jar.set(refresh.name,refresh.value,refresh.options);
 for(const cookie of jar.getAll())if(cookie.name.startsWith('sb-'))jar.delete(cookie.name);
 redirect(next);
}
export async function signup(form:FormData){
 const credentials=fields(form,'/signup','/workspace');let response:Response;
 try{response=await fetch(`${backendUrl()}/api/auth/register`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(credentials),cache:'no-store',signal:AbortSignal.timeout(12000)})}catch{redirect('/signup?error=unavailable')}
 if(!response.ok)redirect(`/signup?error=${response.status===409?'exists':response.status===429?'rate':response.status>=500?'unavailable':'input'}`);
 redirect('/login?notice=created');
}
export async function logout(){try{await logoutSessions()}catch{redirect('/workspace?error=logout')}redirect('/login')}
export async function linkAccount(){redirect('/login')}
