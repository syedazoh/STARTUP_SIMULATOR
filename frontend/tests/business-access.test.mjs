import {test} from 'node:test'
import assert from 'node:assert/strict'
import {readFile} from 'node:fs/promises'
import vm from 'node:vm'
import React from 'react'
import {transformWithEsbuild} from 'vite'
async function render(status,items=[]){
 const context=vm.createContext({});let retries=0
 const exports={react:{default:React,useEffect:()=>{}},'react-redux':{useDispatch:()=>()=>{retries++},useSelector:fn=>fn({business:{status,items}})},'react-router-dom':{Navigate:'navigate',Outlet:'outlet'},'../store/slices/businessSlice':{fetchBusinesses:()=>({type:'retry'})}}
 const source=await readFile(new URL('../src/components/RequireBusiness.jsx',import.meta.url),'utf8')
 const {code}=await transformWithEsbuild("import React from 'react';\n"+source,'RequireBusiness.jsx',{loader:'jsx',jsx:'transform'})
 const module=new vm.SourceTextModule(code,{context});await module.link(name=>new vm.SyntheticModule(Object.keys(exports[name]),function(){for(const [key,value] of Object.entries(exports[name]))this.setExport(key,value)},{context}));await module.evaluate()
 return {tree:module.namespace.default(),retries:()=>retries}
}
function find(node,type){if(!node||typeof node!=='object')return null;if(node.type===type)return node;for(const child of React.Children.toArray(node.props?.children)){const found=find(child,type);if(found)return found}return null}
test('failed business lookup shows recovery instead of misleading new-company onboarding',async()=>{
 const {tree,retries}=await render('failed');assert.equal(find(tree,'navigate'),null);assert.ok(find(tree,'p').props.role==='alert');find(tree,'button').props.onClick();assert.equal(retries(),1)
})
test('only a successful empty business list enters setup; existing companies retain their workspace',async()=>{
 assert.equal((await render('succeeded')).tree.props.to,'/onboarding');assert.equal((await render('succeeded',[{id:'existing'}])).tree.type,'outlet');assert.equal(find((await render('loading')).tree,'navigate'),null)
})
