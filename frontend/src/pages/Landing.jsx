import { Navigate } from 'react-router-dom'
import { useSelector } from 'react-redux'
import {motion,AnimatePresence} from 'framer-motion';
import LandingExperience from '../landing/LandingExperience'
import '../landing/landing.css'
const animation={div:motion.div,span:motion.span,button:motion.button,Presence:AnimatePresence};
const loadThree = () => import('three')
export default function Landing() {
 const token=useSelector(state=>state.auth.token)
 if(token)return <Navigate to="/app" replace />
 return <LandingExperience signupHref="/register" loginHref="/login" loadThree={loadThree} animation={animation} />
}
