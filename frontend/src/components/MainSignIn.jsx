import {useEffect} from 'react'
import {useLocation} from 'react-router-dom'
import {mainLoginUrl} from '../utils/mainLogin.mjs'
export default function MainSignIn({registration=false}){const location=useLocation();const target=mainLoginUrl(import.meta.env.VITE_MAIN_APP_URL||'http://localhost:3000',location.state?.from||'/app',registration);useEffect(()=>{window.location.replace(target)},[target]);return <section className="quick-start"><h1>Opening your main {registration?'registration':'sign-in'}.</h1><p>Use your original Startup Simulator email and password on port 3000. Supabase login is turned off. There is one sign-in for your company and all five departments.</p><a href={target}>Continue to {registration?'registration':'sign in'}</a></section>}
