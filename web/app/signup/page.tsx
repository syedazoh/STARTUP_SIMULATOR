import {signup} from '../actions';
import {nativeNotice} from '../../lib/native-session';
import {Submit} from '../../components/submit';
export default async function Signup({searchParams}:{searchParams:Promise<Record<string,string|undefined>>}){
 const params=await searchParams;
 return <section className="card"><h1>Create your Startup Simulator account</h1><p>This creates a new simulator account. If you already have a business, return to sign in with your original account.</p>{params.error&&<p role="alert" className="error">{nativeNotice(params.error)}</p>}<form action={signup}><label htmlFor="email">Email address</label><input id="email" name="email" type="email" maxLength={254} autoComplete="email" required/><label htmlFor="password">Password</label><input id="password" name="password" type="password" minLength={8} maxLength={128} autoComplete="new-password" required/><Submit>Create account</Submit></form><a href="/login">Return to sign in</a></section>;
}
