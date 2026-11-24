import {test} from 'node:test';import assert from 'node:assert/strict';
import {agentRole,settingsPayload,chatPayload} from '../lib/agent-tools-contracts.ts';
import {linkFailure,workspaceIssue} from '../lib/account-link.ts';
const form=values=>{const f=new FormData();for(const [k,v] of Object.entries(values))f.set(k,String(v));return f};
test('department settings fail closed for unknown roles and arbitrary actions',()=>{
 for(const role of ['../finance','finance/../../tasks','unknown',''])assert.throws(()=>agentRole(role));
 assert.throws(()=>settingsPayload('ceo','mode',form({mode:'manual'})));
 assert.throws(()=>settingsPayload('finance','credentials',form({})));
 assert.throws(()=>settingsPayload('finance','mode',form({mode:'unsafe'})));
});
test('auto mode requires explicit acknowledgement and bounded thresholds; zero stays zero',()=>{
 assert.throws(()=>settingsPayload('hr','mode',form({mode:'auto',mode_max:1})));
 assert.deepEqual(settingsPayload('finance','mode',form({mode:'auto',mode_max:0,acknowledge_auto:'on'})),{mode:'auto',auto_thresholds:{auto_approve_max:0}});
 assert.equal(settingsPayload('finance','mode',form({mode:'manual'})).auto_thresholds.auto_approve_max,null);
 for(const value of ['NaN','Infinity','-1','1000000001',' '])assert.throws(()=>settingsPayload('operations','policy',form({approve_max:value})));
 assert.deepEqual(settingsPayload('hr','policy',form({enabled:'on',approve_max:2,deny_min:4})),{enabled:true,auto_approve_max:2,auto_deny_min:4});
});
test('chat is bounded plain content, not an approval or arbitrary API payload',()=>{
 assert.deepEqual(chatPayload('  Review our budget  '),{content:'Review our budget'});
 for(const value of ['', ' ', 'x'.repeat(4001)])assert.throws(()=>chatPayload(value));
});
test('account linking distinguishes legacy credentials, backend and identity failures without leaking query content',()=>{
 assert.equal(linkFailure(401,'login'),'link_credentials');assert.equal(linkFailure(503,'link'),'link_backend');assert.equal(linkFailure(409,'link'),'link_conflict');assert.equal(linkFailure(403,'link'),'link_identity');assert.equal(linkFailure(429,'login'),'link_rate');
 for(const code of ['link_credentials','link_backend','link_identity','__proto__','<script>bad</script>'])assert.equal(typeof workspaceIssue(code),'string');
 assert.ok(!workspaceIssue('<script>bad</script>').includes('<script>'));
});
