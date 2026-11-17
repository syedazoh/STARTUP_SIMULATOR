import {test} from 'node:test';
import assert from 'node:assert/strict';
import {businessPayload, departmentCommand, requireDecision, decisionAllowed, goalPayload} from '../lib/workspace-contracts.ts';
const form = (v) => {const f = new FormData(); for (const [k,val] of Object.entries(v)) f.set(k, String(val)); return f;};
const valid = {company_name:' Startup ', industry:'Software', starting_budget:10000, starting_customer_base:0, starting_headcount:2, starting_resources:100};
test('business identity and agents are server selected; numeric zero preserved', () => {
 const p=businessPayload(form({...valid, owner_user_id:'victim', enabled_agents:'unknown'}));
 assert.equal(p.company_name,'Startup'); assert.equal(p.starting_customer_base,0);
 assert.equal(p.owner_user_id,undefined); assert.equal(p.enabled_agents.length,5);
});
test('invalid financial and count inputs fail before a request', () => {
 for (const v of ['', ' ', 'Infinity', 'NaN', '-1', '1000000001']) assert.throws(()=>businessPayload(form({...valid, starting_budget:v})));
 for (const v of ['0.5', '-1', 'NaN']) assert.throws(()=>businessPayload(form({...valid, starting_headcount:v})));
 assert.throws(()=>businessPayload(form({...valid, company_name:' '})));
});
test('department forms expose only bounded simulation commands', () => {
 for (const [agent,values,path] of [
 ['finance',{amount:25,department:'Marketing'},'budget-request'],
 ['marketing',{campaign_name:'Launch',requested_budget:250},'campaign-launch'],
 ['hr',{role:'Designer',headcount:1,monthly_salary:500},'recruitment-request'],
 ['operations',{resource_type:'Stock',quantity:5,unit_cost:20},'resource-request']]) assert.ok(departmentCommand(agent,form(values)).path.endsWith(path));
 for (const agent of ['ceo','instagram','../finance','']) assert.throws(()=>departmentCommand(agent,form({})));
 assert.throws(()=>departmentCommand('hr',form({role:'Designer',headcount:1.5,monthly_salary:500})));
});
test('decisions fail closed for other business, live publishing, stale status or forged decision', () => {
 const task={business_id:'a',action_type:'budget_request',status:'pending_approval'};
 requireDecision(task,'a','approve'); requireDecision(task,'a','reject');
 assert.throws(()=>requireDecision(task,'b','approve'));
 assert.throws(()=>requireDecision(task,'a','release-budget'));
 for(const action_type of ['instagram_post','reel_request','unknown']) assert.equal(decisionAllowed({...task,action_type}),false);
 for(const status of ['executed','rejected','approved','ceo_reviewing','needs_changes']) assert.throws(()=>requireDecision({...task,status},'a','approve'));
});
test('goal is trimmed, bounded and never accepts file input',()=>{
 assert.equal(goalPayload(form({goal:'  Launch a product  '})).goal,'Launch a product');
 for(const goal of ['x',' ', 'a'.repeat(2001)]) assert.throws(()=>goalPayload(form({goal})));
});

test('API errors distinguish identity, dependency and validation failures without echoing inputs', async()=>{
 const {apiError}=await import('../lib/api-errors.ts');
 assert.match(apiError(401,{},'/api/businesses'),/session ended/);
 assert.match(apiError(403,{},'/api/tasks/x'),/do not have access/);
 assert.match(apiError(503,{detail:'private connection string'},'/api/businesses'),/unavailable/);
 assert.doesNotMatch(apiError(503,{detail:'private connection string'},'/api/businesses'),/connection string/);
 assert.match(apiError(409,{},'/api/auth/me'),/Link your original/);
 assert.equal(apiError(409,{detail:'Proposal changed'},'/api/tasks/x'),'Proposal changed');
 const error=apiError(422,{detail:[{loc:['body','goal'],msg:'Too short',input:'SECRET'}]},'/api/businesses/a/ceo/plans');
 assert.match(error,/goal.*Too short/); assert.doesNotMatch(error,/SECRET/);
});


test('database timestamps without offsets are interpreted as UTC, not viewer local time', async()=>{
 const {utcInstant}=await import('../lib/workspace-contracts.ts');
 assert.equal(utcInstant('2026-11-16T12:00:00').toISOString(),'2026-11-16T12:00:00.000Z');
 assert.equal(utcInstant('2026-11-16T17:00:00+05:00').toISOString(),'2026-11-16T12:00:00.000Z');
 assert.equal(utcInstant('not-a-date'),null);
});
