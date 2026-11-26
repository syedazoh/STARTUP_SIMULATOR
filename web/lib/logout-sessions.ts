import 'server-only';
import {cookies} from 'next/headers';
import {ACCESS_COOKIE,REFRESH_COOKIE,backendUrl,validRefresh,accessOptions} from './native-session';
export async function logoutSessions(accessOverride?:string){
 const jar=await cookies(),refresh=jar.get(REFRESH_COOKIE)?.value,access=jar.get(ACCESS_COOKIE)?.value||accessOverride;
 if(refresh||access){
 const headers:Record<string,string>={'X-Requested-With':'XMLHttpRequest'};
 if(refresh&&validRefresh(refresh))headers.Cookie=`${REFRESH_COOKIE}=${refresh}`;
 if(access)headers.Authorization=`Bearer ${access}`;
 const response=await fetch(`${backendUrl()}/api/auth/logout`,{method:'POST',headers,cache:'no-store',redirect:'error',signal:AbortSignal.timeout(12000)});
 if(!response.ok)throw new Error('Could not revoke your session. Retry.');
 }
 for(const cookie of jar.getAll())if(cookie.name.startsWith('sb-'))jar.delete(cookie.name);
 jar.set(REFRESH_COOKIE,'',{...accessOptions(),path:'/api/auth',maxAge:0});
 for(const name of [ACCESS_COOKIE,REFRESH_COOKIE])jar.set(name,'',{...accessOptions(),maxAge:0});
 jar.set('startup-pending-email','',{...accessOptions(),path:'/login',maxAge:0});
}
