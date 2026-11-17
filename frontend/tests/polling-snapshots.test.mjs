import {test} from 'node:test'
import assert from 'node:assert/strict'
import vm from 'node:vm'
import {readFile} from 'node:fs/promises'
import toolkit from '@reduxjs/toolkit'
async function load(name, api = {get:async()=>({data:[]})}) {
 const source=await readFile(new URL(`../src/store/slices/${name}Slice.js`,import.meta.url),'utf8')
 const context=vm.createContext({console})
 const mod=new vm.SourceTextModule(source,{context})
 await mod.link(specifier=>{
  const values=specifier==='@reduxjs/toolkit'?{createSlice:toolkit.createSlice,createAsyncThunk:toolkit.createAsyncThunk}:{default:api}
  return new vm.SyntheticModule(Object.keys(values),function(){for(const [k,v] of Object.entries(values))this.setExport(k,v)},{context})
 });await mod.evaluate();return {reducer:mod.namespace.default,fetch:mod.namespace[name==='agents'?'fetchAgents':'fetchEvents'], actions:mod.namespace}
}
for(const name of ['agents','events'])test(`${name}: background polls preserve visible snapshots, errors and latest response ordering`,async()=>{
 const {reducer,fetch}=await load(name), key=name==='agents'?'statuses':'items'
 const snapshot=name==='agents'?{finance:{},marketing:{},hr:{},operations:{},ceo:{}}:Array.from({length:11},(_,i)=>({event_id:String(i)}))
 let state=reducer(undefined,{type:'init'})
 state=reducer(state,fetch.pending('first','business'))
 assert.equal(state.loadStatus,'loading')
 state=reducer(state,fetch.fulfilled(snapshot,'first','business'))
 const count=Object.keys(state[key]).length
 state=reducer(state,fetch.pending('second','business'))
 assert.equal(state.loadStatus,'succeeded');assert.equal(Object.keys(state[key]).length,count)
 state=reducer(state,fetch.rejected(new Error('offline'),'second','business'))
 assert.equal(state.loadStatus,'succeeded');assert.equal(Object.keys(state[key]).length,count);assert.match(state.error,/offline/)
 state=reducer(state,fetch.pending('old','business'));state=reducer(state,fetch.pending('new','business'))
 state=reducer(state,fetch.fulfilled(name==='agents'?{}:[],'new','business'))
 state=reducer(state,fetch.fulfilled(snapshot,'old','business'))
 assert.equal(Object.keys(state[key]).length,0);assert.equal(state.error,null)
})


for (const name of ['agents','events']) test(`${name}: slow refresh requests never overlap or starve the displayed update`, async()=>{
 let release, calls=0
 const {reducer,fetch}=await load(name,{get:()=>{calls++;return new Promise(resolve=>{release=resolve})}})
 const store=toolkit.configureStore({reducer:{[name]:reducer}})
 const first=store.dispatch(fetch('business'))
 await store.dispatch(fetch('business'))
 assert.equal(calls,1)
 release({data:name==='agents'?{ceo:{}}:[{event_id:'one'}]})
 await first
 assert.equal(store.getState()[name].hasSnapshot,true)
 assert.equal(store.getState()[name].isRefreshing,false)
})

test('request changes replaces the actionable task instead of hiding and re-adding it',async()=>{
 const {reducer,actions}=await load('tasks')
 let state=reducer(undefined,actions.fetchPendingTasks.fulfilled([{id:'task',status:'pending_approval',payload:{amount:1000}}],'read','business'))
 state=reducer(state,actions.requestTaskChanges.fulfilled({id:'task',status:'pending_approval',payload:{amount:400}},'revise',{}))
 assert.equal(state.items.length,1);assert.equal(state.items[0].payload.amount,400)
 state=reducer(state,actions.requestTaskChanges.fulfilled({id:'task',status:'needs_changes',revision_error:'AI unavailable'},'retry',{}))
 assert.equal(state.items.length,1);assert.equal(state.items[0].revision_error,'AI unavailable')
})
