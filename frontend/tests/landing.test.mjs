import test from 'node:test';
import assert from 'node:assert/strict';
import {INTRODUCTIONS,nextIntroduction,initialTheme} from '../src/landing/agents.mjs';
test('landing theme respects a stored choice before device preference',()=>{
 assert.equal(initialTheme('light',true),'light');assert.equal(initialTheme('dark',false),'dark');
 assert.equal(initialTheme(null,true),'dark');assert.equal(initialTheme('invalid',false),'light');
});
test('guided introductions cover all departments with captions and bounded navigation',()=>{
 assert.deepEqual(INTRODUCTIONS.map(a=>a.id),['ceo','finance','marketing','hr','operations']);
 assert.ok(INTRODUCTIONS.every(a=>a.speech.length>100&&a.description&&a.example));
 assert.equal(nextIntroduction(4),0);assert.equal(nextIntroduction(0,-1),4);
});

const {LAUNCH_STEPS,nextLaunchStep,participantName}=await import('../src/landing/launch-scenario.mjs');
test('synthetic launch explains every department and keeps owner approval distinct',()=>{
 assert.equal(new Set(LAUNCH_STEPS.map(s=>s.id)).size,LAUNCH_STEPS.length);
 const participants=new Set(LAUNCH_STEPS.flatMap(s=>[s.sender,s.receiver]));
 assert.deepEqual([...participants].sort(),['ceo','finance','hr','marketing','operations','owner']);
 const review=LAUNCH_STEPS.findIndex(s=>s.id==='approval');
 const approval=LAUNCH_STEPS.findIndex(s=>s.id==='owner-preview');
 const execute=LAUNCH_STEPS.findIndex(s=>s.id==='execution');
 assert.ok(review<approval&&approval<execute);
 assert.equal(LAUNCH_STEPS[review].receiver,'owner');
 assert.equal(LAUNCH_STEPS[approval].sender,'owner');
 assert.match(LAUNCH_STEPS[approval].detail,/no real authority/);
 assert.ok(LAUNCH_STEPS.every(s=>s.sender!==s.receiver&&s.detail&&s.artifact));
 assert.equal(nextLaunchStep(0,-1),0);
 assert.equal(nextLaunchStep(LAUNCH_STEPS.length-1),LAUNCH_STEPS.length-1);
 assert.equal(participantName('owner'),'You · Owner');
});
