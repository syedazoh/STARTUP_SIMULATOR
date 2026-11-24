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
