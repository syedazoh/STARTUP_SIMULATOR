import {cookies} from 'next/headers';
import {redirect} from 'next/navigation';
import {ACCESS_COOKIE,nativeUser,nativeNotice} from '../../lib/native-session';
import {safeReturnTo} from '../../lib/login-flow';
import {login} from '../actions';
import {Submit} from '../../components/submit';
export default async function Login({searchParams}:{searchParams:Promise<Record<string,string|undefined>>}){
 const params=await searchParams,next=safeReturnTo(params.next);let signedIn=false;
 try{signedIn=!!await nativeUser((await cookies()).get(ACCESS_COOKIE)?.value)}catch{}
 if(signedIn)redirect(next);
 return <section className="card"><h1>Sign in to Startup Simulator</h1><p>Use your original Startup Simulator email and password. Supabase sign-in and email codes are turned off for now.</p>{params.error&&<p role="alert" className="error">{nativeNotice(params.error)}</p>}{params.notice==='created'&&<p role="status">{nativeNotice('created')}</p>}<form action={login}><input type="hidden" name="next" value={next}/><label htmlFor="email">Email address</label><input id="email" name="email" type="email" autoComplete="username" maxLength={254} required/><label htmlFor="password">Password</label><input id="password" name="password" type="password" autoComplete="current-password" minLength={8} maxLength={128} required/><Submit>Sign in</Submit></form><p>New user? <a href="/signup">Create an account</a>. Already had a business? Sign in to the original account; no account linking is needed.</p></section>;
}
