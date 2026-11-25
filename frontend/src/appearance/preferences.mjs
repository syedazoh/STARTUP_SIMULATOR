export const DEFAULT_APPEARANCE = {preset:'glass',mode:'system',motion:true,palette:'lavender'};
export const PRESETS = [
 {id:'glass',name:'Executive Glass',description:'Purple glass, warm highlights.'},
 {id:'water',name:'Pearl Water',description:'Pearl reflections, flowing contours.'},
 {id:'monolith',name:'Monolith',description:'Matte surfaces, sculpted beige.'},
];
export function normalizeAppearance(value){return {preset:PRESETS.some(p=>p.id===value?.preset)?value.preset:'glass',mode:['light','dark','system'].includes(value?.mode)?value.mode:'system',motion:typeof value?.motion==='boolean'?value.motion:true,palette:['emerald','champagne','lavender'].includes(value?.palette)?value.palette:'lavender'}}
export function resolveTheme(mode,dark){return mode==='system'?(dark?'dark':'light'):mode}
