import { Navigate } from 'react-router-dom'
import { useSelector } from 'react-redux'
import LandingExperience from '../landing/LandingExperience'
import '../landing/landing.css'
export default function Landing() {
 const token=useSelector(state=>state.auth.token)
 if(token)return <Navigate to="/app" replace />
 return <LandingExperience signupHref="/register" loginHref="/login" />
}
