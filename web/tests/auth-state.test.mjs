import test from 'node:test';
import assert from 'node:assert/strict';
import {authConfigurationIssue,authErrorCode,signupDestination} from '../lib/auth-state.ts';
const configured={NEXT_PUBLIC_SUPABASE_URL:'https://project.supabase.co',NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY:'public-test-key'};
test('missing and placeholder provider configuration is actionable before submitting',()=>{
 assert.ok(authConfigurationIssue({}));assert.ok(authConfigurationIssue({...configured,NEXT_PUBLIC_SUPABASE_URL:'https://YOUR_PROJECT.supabase.co'}));
 assert.equal(authConfigurationIssue(configured),null);
 assert.ok(authConfigurationIssue({...configured,NEXT_PUBLIC_SUPABASE_URL:'https://user:password@project.supabase.co'}));
 assert.ok(authConfigurationIssue({...configured,NEXT_PUBLIC_SUPABASE_URL:'http://external.example.com'}));
 assert.equal(authConfigurationIssue({...configured,NEXT_PUBLIC_SUPABASE_URL:'http://127.0.0.1:8012'}),null);
});
test('signup without required confirmation uses the valid returned session',()=>{
 assert.equal(signupDestination(true),'/workspace');assert.equal(signupDestination(false),'/login?notice=verify');
});
test('authentication errors distinguish connectivity, confirmation, rate limits and credentials',()=>{
 assert.equal(authErrorCode({status:503}),'unavailable');assert.equal(authErrorCode({name:'AuthRetryableFetchError'}),'unavailable');
 assert.equal(authErrorCode({status:429}),'rate');assert.equal(authErrorCode({code:'email_not_confirmed'}),'confirmation');assert.equal(authErrorCode({status:400}),'login');
});
