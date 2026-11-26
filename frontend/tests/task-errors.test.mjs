import {test} from 'node:test'
import assert from 'node:assert/strict'
import {readFile} from 'node:fs/promises'
import vm from 'node:vm'
import toolkit from '@reduxjs/toolkit'

async function tasks(post) {
 const context=vm.createContext({})
 const source=await readFile(new URL('../src/store/slices/tasksSlice.js',import.meta.url),'utf8')
 const redux=new vm.SyntheticModule(['createAsyncThunk','createSlice'],function(){for(const key of ['createAsyncThunk','createSlice'])this.setExport(key,toolkit[key])},{context})
 const api=new vm.SyntheticModule(['default'],function(){this.setExport('default',{post})},{context})
 const module=new vm.SourceTextModule(source,{context});await module.link(name=>name==='@reduxjs/toolkit'?redux:api);await module.evaluate()
 return {actions:module.namespace,store:toolkit.configureStore({reducer:module.namespace.default,preloadedState:{items:[{id:'task-1',status:'pending_approval'}],status:'succeeded',error:null}})}
}
test('failed approval preserves the actual budget conflict and the pending task',async()=>{
 const message='Insufficient unreserved funds for this task'
 const {actions,store}=await tasks(async()=>{throw {response:{status:409,data:{detail:message}}}})
 await assert.rejects(store.dispatch(actions.approveTask({taskId:'task-1',expectedFingerprint:'reviewed'})).unwrap(),error=>error===message)
 assert.equal(store.getState().items.length,1)
})
test('approval keeps the exact reviewed fingerprint and removes only a successful task',async()=>{
 let body;const {actions,store}=await tasks(async(_url,payload)=>{body=payload;return {data:{id:'task-1'}}})
 await store.dispatch(actions.approveTask({taskId:'task-1',expectedFingerprint:'reviewed'})).unwrap()
 assert.equal(body.expected_fingerprint,'reviewed');assert.equal(store.getState().items.length,0)
})
test('unexpected server errors do not expose backend diagnostics or delete the task',async()=>{
 const {actions,store}=await tasks(async()=>{throw {response:{status:500,data:{detail:'Private backend trace'}}}})
 await assert.rejects(store.dispatch(actions.rejectTask({taskId:'task-1',ownerFeedback:'No'})).unwrap(),error=>typeof error==='string'&&!error.includes('Private')&&error.includes('refresh'))
 assert.equal(store.getState().items.length,1)
})
