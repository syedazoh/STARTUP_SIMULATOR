/** Existing FastAPI sessions remain the authentication and revocation authority. */
export const ACCESS_COOKIE='startup_access';
export const REFRESH_COOKIE='simulator_refresh';
export const backendUrl=()=>process.env.BACKEND_URL||'http://127.0.0.1:8000';
export const validRefresh=(value:string)=>/^[A-Za-z0-9_-]{20,512}$/.test(value);
export function accessOptions(){return {httpOnly:true,secure:process.env.NODE_ENV==='production',sameSite:'strict' as const,path:'/',maxAge:3600}}
export function refreshedCookie(response:Response){
 const value=response.headers.getSetCookie().findLast(value=>value.startsWith(`${REFRESH_COOKIE}=`)&&!value.startsWith(`${REFRESH_COOKIE}=;`));
 if(!value)return null;const token=value.split(';')[0].slice(REFRESH_COOKIE.length+1);if(!validRefresh(token))return null;
 return {name:REFRESH_COOKIE,value:token,options:{...accessOptions(),maxAge:Math.min(2592000,Number(value.match(/Max-Age=(\d+)/i)?.[1]||604800))}};
}
export async function nativeUser(access:string|undefined){
 if(!access)return null;
 const response=await fetch(`${backendUrl()}/api/auth/me`,{headers:{Authorization:`Bearer ${access}`},cache:'no-store',signal:AbortSignal.timeout(12000)});
 if(response.status===401)return null;if(!response.ok)throw new Error('Account service unavailable. Check backend health.');return response.json();
}
export async function restoreNative(access:string|undefined,refresh:string|undefined){
 if(access&&await nativeUser(access))return {access,response:null};
 if(!refresh||!validRefresh(refresh))return null;
 const response=await fetch(`${backendUrl()}/api/auth/refresh`,{method:'POST',headers:{Cookie:`${REFRESH_COOKIE}=${refresh}`,'X-Requested-With':'XMLHttpRequest'},cache:'no-store',signal:AbortSignal.timeout(12000)});
 if(response.status===401)return null;if(!response.ok)throw new Error('Session service unavailable. Retry shortly.');
 const body=await response.json();if(typeof body.access_token!=='string')throw new Error('Invalid session response');
 return {access:body.access_token as string,response};
}
export function nativeNotice(code?:string){
 if(code==='input')return 'Enter your email and a password between 8 and 128 characters.';
 if(code==='unavailable')return 'Cannot reach the backend. Start FastAPI on port 8000 and check MongoDB connectivity.';
 if(code==='rate')return 'Too many sign-in attempts. Wait a minute before retrying.';
 if(code==='exists')return 'This email already has an account. Sign in with its original password.';
 if(code==='created')return 'Account created. Sign in with the password you just chose.';
 return 'Invalid email or password. Use your original Startup Simulator password, which may differ from your Supabase password.';
}
