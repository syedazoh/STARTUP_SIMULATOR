"use client";
import {useEffect,useState} from 'react';
import {usePathname} from 'next/navigation';
import Atmosphere from '../../frontend/src/landing/Atmosphere';
const loadThree=()=>import('three');
export default function WorkspaceVisuals(){const path=usePathname();const [enabled,setEnabled]=useState(true),[reduced,setReduced]=useState(false);
 useEffect(()=>{const preference=matchMedia('(prefers-reduced-motion: reduce)');setReduced(preference.matches);try{setEnabled(localStorage.getItem('startup-workspace-motion')!=='off')}catch{}const update=()=>setReduced(preference.matches);preference.addEventListener('change',update);return()=>preference.removeEventListener('change',update)},[]);
 if(!path.startsWith('/workspace'))return null;
 return <><div className="workspace-effects"><Atmosphere loadThree={loadThree} enabled={enabled&&!reduced} theme="dark"/></div><button className="workspace-motion-toggle" disabled={reduced} aria-pressed={enabled&&!reduced} title={reduced?'Reduced motion follows your device setting':'Toggle decorative background motion'} onClick={()=>{setEnabled(!enabled);try{localStorage.setItem('startup-workspace-motion',enabled?'off':'on')}catch{}}}>Background motion {enabled&&!reduced?'on':'off'}</button></>;
}
