'use client';
import {useEffect,useRef} from 'react';
// Decorative real geometry only; no product state, data or network effects.
export default function Atmosphere({loadThree,enabled,theme}) {
 const canvas=useRef(null),controls=useRef(null),latest=useRef({enabled,theme});latest.current={enabled,theme};
 useEffect(()=>{
  let disposed=false,cleanup=()=>{};
  loadThree().then(THREE=>{
   if(disposed||!canvas.current)return;
   const renderer=new THREE.WebGLRenderer({canvas:canvas.current,alpha:true,antialias:false,powerPreference:'low-power'});
   renderer.setPixelRatio(Math.min(devicePixelRatio||1,1.25));
   const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(40,1,.1,30);camera.position.z=9;
   const material=new THREE.MeshStandardMaterial({color:'#9367cf',metalness:.75,roughness:.27});
   const geometry=new THREE.TorusKnotGeometry(2.3,.42,128,14,2,3),sculpture=new THREE.Mesh(geometry,material);scene.add(sculpture);sculpture.position.set(2.8,.3,0);sculpture.rotation.set(.5,.25,.4);
   scene.add(new THREE.HemisphereLight('#e4d5ff','#251539',2.5));
   const key=new THREE.DirectionalLight('#ecd9bd',5);key.position.set(-3,5,4);scene.add(key);
   const rim=new THREE.DirectionalLight('#9860f7',6);rim.position.set(4,-2,2);scene.add(rim);
   let frame=0,last=0,visible=true;
   const draw=()=>renderer.render(scene,camera);
   const tick=now=>{if(disposed)return;if(visible&&!document.hidden&&now-last>33){sculpture.rotation.y+=.002;sculpture.rotation.z+=.0008;draw();last=now}frame=requestAnimationFrame(tick)};
   const sync=()=>{cancelAnimationFrame(frame);material.color.set(latest.current.theme==='dark'?'#9367cf':'#b59acc');draw();if(latest.current.enabled)frame=requestAnimationFrame(tick)};
   const resize=()=>{const box=canvas.current?.getBoundingClientRect();if(!box)return;camera.aspect=box.width/box.height;camera.updateProjectionMatrix();renderer.setSize(box.width,box.height,false);draw()};
   const observer=new ResizeObserver(resize);observer.observe(canvas.current);
   const intersection=new IntersectionObserver(([entry])=>{visible=entry.isIntersecting;if(visible)draw()});intersection.observe(canvas.current);
   const visibility=()=>{if(!document.hidden)draw()};document.addEventListener('visibilitychange',visibility);
   controls.current={sync};resize();sync();
   cleanup=()=>{controls.current=null;cancelAnimationFrame(frame);observer.disconnect();intersection.disconnect();document.removeEventListener('visibilitychange',visibility);geometry.dispose();material.dispose();renderer.dispose()};
  }).catch(()=>{/* The themed CSS atmosphere remains without WebGL. */});
  return()=>{disposed=true;cleanup()};
 },[loadThree]);
 useEffect(()=>{controls.current?.sync()},[enabled,theme]);
 return <div className="launch-sculpture" aria-hidden="true"><canvas ref={canvas}/></div>;
}
