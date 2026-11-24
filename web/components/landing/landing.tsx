"use client";
import {motion,AnimatePresence} from 'framer-motion';
import LandingExperience from "../../../frontend/src/landing/LandingExperience";
import "./landing.css";
// Resolve Three.js from the app that owns the dependency, not shared source.
const animation={div:motion.div,span:motion.span,button:motion.button,Presence:AnimatePresence};
const loadThree = () => import("three");
export default function Landing() { return <LandingExperience signupHref="/signup" loginHref="/login" loadThree={loadThree} animation={animation} />; }
