import 'server-only';
import {cookies} from 'next/headers';
import {supabase} from './supabase';
export async function logoutSessions(){
 const jar=await cookies(),refresh=jar.get('simulator_refresh')?.value;
 if(refresh){if(!/^[A-Za-z0-9_-]{20,512}$/.test(refresh))throw new Error('Invalid session cookie.');const response=await fetch(`${process.env.BACKEND_URL||'http://127.0.0.1:8000'}/api/auth/logout`,{method:'POST',headers:{Cookie:`simulator_refresh=${refresh}`,'X-Requested-With':'XMLHttpRequest'},cache:'no-store',redirect:'error',signal:AbortSignal.timeout(12000)});if(!response.ok)throw new Error('Could not end the classic session. Retry before leaving.');}
 const client=await supabase();const {error}=await client.auth.signOut();if(error)throw new Error('Could not end the Supabase session. Retry.');jar.set('startup-pending-email','',{path:'/login',maxAge:0,httpOnly:true,sameSite:'lax',secure:process.env.NODE_ENV==='production'});jar.set('simulator_refresh','',{path:'/',maxAge:0,httpOnly:true,sameSite:'strict',secure:process.env.NODE_ENV==='production'});jar.set('simulator_refresh','',{path:'/api/auth',maxAge:0,httpOnly:true,sameSite:'strict',secure:process.env.NODE_ENV==='production'});
}
