'use client';
import {useAppearance} from '../appearance/Appearance';
import {useEffect,useRef} from 'react';
// Decorative real geometry only; no product state, data or network effects.
export default function Atmosphere({loadThree,enabled,theme}) {
 const {preferences}=useAppearance();
 const canvas=useRef(null),controls=useRef(null),latest=useRef({enabled,theme,preset:preferences.preset,palette:preferences.palette});latest.current={enabled,theme,preset:preferences.preset,palette:preferences.palette};
 useEffect(()=>{
  let disposed=false,cleanup=()=>{};
  loadThree().then(THREE=>{
   if(disposed||!canvas.current)return;
   const renderer=new THREE.WebGLRenderer({canvas:canvas.current,alpha:true,antialias:false,powerPreference:'low-power'});
   renderer.setPixelRatio(Math.min(devicePixelRatio||1,1.25));
   const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(40,1,.1,30);camera.position.z=9;
   const material=new THREE.MeshStandardMaterial({color:'#9367cf',metalness:.75,roughness:.27});
   const geometry=new THREE.TorusKnotGeometry(2.3,.42,128,14,2,3),sculpture=new THREE.Mesh(geometry,material);const waterGeometry=new THREE.SphereGeometry(2.2,48,32),monolithGeometry=new THREE.BoxGeometry(2.4,4.4,.9);const points=waterGeometry.attributes.position;for(let i=0;i<points.count;i++){const x=points.getX(i),y=points.getY(i),z=points.getZ(i),scale=1+.055*Math.sin(y*4+x*2)*Math.cos(z*3);points.setXYZ(i,x*scale,y*scale,z*scale)}waterGeometry.computeVertexNormals();scene.add(sculpture);sculpture.position.set(2.8,.3,0);sculpture.rotation.set(.5,.25,.4);
   scene.add(new THREE.HemisphereLight('#e4d5ff','#251539',2.5));
   const key=new THREE.DirectionalLight('#ecd9bd',5);key.position.set(-3,5,4);scene.add(key);
   const rim=new THREE.DirectionalLight('#9860f7',6);rim.position.set(4,-2,2);scene.add(rim);
   let frame=0,last=0,visible=true;
   const draw=()=>renderer.render(scene,camera);
   const tick=now=>{if(disposed)return;if(visible&&!document.hidden&&now-last>33){sculpture.rotation.y+=.002;sculpture.rotation.z+=.0008;draw();last=now}frame=requestAnimationFrame(tick)};
   const sync=()=>{cancelAnimationFrame(frame);rim.color.set(latest.current.palette==='emerald'?'#65b795':latest.current.palette==='champagne'?'#bba078':'#9860f7');const preset=latest.current.preset;sculpture.geometry=preset==='water'?waterGeometry:preset==='monolith'?monolithGeometry:geometry;material.color.set(preset==='glass'?'#e6d6ba':preset==='water'?'#d0bce3':'#c4ae89');material.roughness=preset==='monolith'?.85:preset==='water'?.08:.27;sculpture.scale.setScalar(preset==='monolith'?.7:1);draw();if(latest.current.enabled)frame=requestAnimationFrame(tick)};
   const resize=()=>{const box=canvas.current?.getBoundingClientRect();if(!box)return;camera.aspect=box.width/box.height;camera.updateProjectionMatrix();renderer.setSize(box.width,box.height,false);draw()};
   const observer=new ResizeObserver(resize);observer.observe(canvas.current);
   const intersection=new IntersectionObserver(([entry])=>{visible=entry.isIntersecting;if(visible)draw()});intersection.observe(canvas.current);
   const visibility=()=>{if(!document.hidden)draw()};document.addEventListener('visibilitychange',visibility);
   controls.current={sync};resize();sync();
   cleanup=()=>{controls.current=null;cancelAnimationFrame(frame);observer.disconnect();intersection.disconnect();document.removeEventListener('visibilitychange',visibility);geometry.dispose();waterGeometry.dispose();monolithGeometry.dispose();material.dispose();renderer.dispose()};
  }).catch(()=>{/* The themed CSS atmosphere remains without WebGL. */});
  return()=>{disposed=true;cleanup()};
 },[loadThree]);
 useEffect(()=>{controls.current?.sync()},[enabled,theme,preferences.preset,preferences.palette]);
 return <div className="launch-sculpture" aria-hidden="true"><canvas ref={canvas}/></div>;
}
