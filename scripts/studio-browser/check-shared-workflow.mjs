/** Isolated real app acceptance. Run shared_workflow_backend.py + production Next :3025. */
import {createRequire} from 'node:module';
import {mkdir,writeFile} from 'node:fs/promises';
const require=createRequire(new URL('../../web/package.json',import.meta.url));
const {chromium}=require('playwright');
const {expect}=require('playwright/test');
const origin=process.env.MAIN_ORIGIN||'http://localhost:3025';
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
const context=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
await context.addInitScript(()=>{
 window.__speech={spoken:[],cancelled:0,recognition:null};
 class Recognition {constructor(){window.__speech.recognition=this}start(){}stop(){this.onend?.()}abort(){this.onend?.()}}
 window.SpeechRecognition=Recognition;
 window.SpeechSynthesisUtterance=class{constructor(text){this.text=text}};
 Object.defineProperty(window,'speechSynthesis',{value:{speak(u){window.__speech.spoken.push(u.text)},cancel(){window.__speech.cancelled++},getVoices(){return []}}});
});
const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
const checks=[];
try{
 const email=`workflow-${Date.now()}@example.com`;
 const registered=await context.request.post('http://localhost:8013/api/auth/register',{data:{email,password:'fixture-password'}});if(registered.status()!==201)throw Error('Fixture registration failed');
 await page.goto(origin+'/login');
 await page.getByLabel('Email address').fill(email);await page.getByLabel('Password',{exact:true}).fill('fixture-password');await page.getByRole('button',{name:'Sign in',exact:true}).click();await page.waitForURL('**/workspace');
 await page.getByRole('button',{name:'Open fictional five-agent demo',exact:true}).click();await page.waitForURL('**/agents/ceo');
 const bid=new URL(page.url()).pathname.split('/')[2],root=`${origin}/workspace/${bid}`;
 const workflow=()=>page.getByRole('region',{name:/shared workflow/});
 await expect(workflow().getByRole('heading',{name:'Work with CEO.'})).toBeVisible();
 const turn=async text=>{const w=workflow();const before=await w.locator('.workflow-conversation>article').count();await w.getByLabel('Message ',{exact:false}).fill(text);await w.getByRole('button',{name:'Send message',exact:true}).click();await expect(w.locator('.workflow-conversation>article')).toHaveCount(before+1,{timeout:20000});};
 await turn('Draft a launch plan for our desk kit.');
 await workflow().getByLabel('Launch goal',{exact:true}).fill('Launch the fictional desk kit after reviewing all four department submissions.');
 await workflow().getByLabel('Proposed deadline',{exact:true}).fill('2026-12-05T17:00');
 await workflow().getByRole('button',{name:'Save launch plan',exact:true}).click();
 const plan=workflow().locator('.workflow-workbench section').filter({has:page.getByRole('heading',{name:'Coordinate a launch'})});
 await expect(plan.locator('details')).toHaveCount(1,{timeout:15000});await plan.locator('summary').click();await plan.getByRole('button',{name:'Authorize & assign four follow-ups',exact:true}).click();
 await expect(workflow().locator('[data-workflow-task]')).toHaveCount(4,{timeout:15000});console.log('CHECKPOINT',page.url());checks.push('Native login; separate demo; CEO draft + explicit four-role assignment.');
 for(const role of ['strategy','finance','marketing','operations']){
  await page.goto(`${root}/agents/${role}`);const w=workflow();await expect(w.locator('[data-workflow-task]')).toHaveCount(1,{timeout:15000});
  await w.getByRole('button',{name:'Discuss this assignment',exact:true}).click();await w.getByRole('button',{name:'Send message',exact:true}).click();await expect(w.locator('.workflow-artifacts [data-artifact]')).toHaveCount(1,{timeout:15000});
  if(['marketing','strategy'].includes(role)){
   await w.getByLabel(`Image brief for ${role==='marketing'?'Marketing':'Strategy'}`).fill('Illustrate a fictional desk kit in purple and warm beige.');await w.getByRole('button',{name:'Generate draft visual',exact:true}).click();
   await expect(w.getByRole('button',{name:'Preview image',exact:true})).toHaveCount(1,{timeout:20000});await w.getByRole('button',{name:'Preview image',exact:true}).click();await expect(w.locator('.workflow-artifacts img')).toBeVisible();
   const download=page.waitForEvent('download');await w.getByRole('button',{name:'Download image',exact:true}).click();await download;
   await w.getByRole('button',{name:'Revise image',exact:true}).click();await w.getByLabel(`Image brief for ${role==='marketing'?'Marketing':'Strategy'}`).fill('Change the background to warm beige.');await w.getByRole('button',{name:'Generate draft visual',exact:true}).click();await expect(w.getByRole('button',{name:'Preview image',exact:true})).toHaveCount(2,{timeout:20000});await w.getByLabel('Include in next submission').first().check();
  }
  await w.getByRole('button',{name:'Submit this version to CEO',exact:true}).click();await expect(w.locator('[data-workflow-task]')).toContainText('Review exact saved submission',{timeout:15000});
 }
 console.log('CHECKPOINT',page.url());checks.push('Four personal workspaces submit linked artifacts. Marketing and Strategy use the same image jobs, preview/download/revision; original retained.');
 await page.goto(`${root}/boardroom`);let w=workflow();await expect(w.locator('[data-workflow-task]')).toHaveCount(4,{timeout:15000});
 const strategy=w.locator('[data-workflow-task]').filter({has:page.locator('header strong',{hasText:'Strategy'})});await strategy.getByText('Review exact saved submission',{exact:true}).click();await strategy.getByLabel('Review feedback').fill('Focus the revised positioning on small remote teams.');await strategy.getByRole('button',{name:'Request changes',exact:true}).click();await expect(strategy).toContainText('needs changes',{timeout:15000});
 await page.goto(`${root}/agents/strategy`);w=workflow();await expect(w.locator('.workflow-feedback')).toContainText('small remote teams',{timeout:15000});await w.getByRole('button',{name:'Discuss this assignment',exact:true}).click();await w.getByRole('button',{name:'Send message',exact:true}).click();await expect(w.getByRole('button',{name:'Submit this version to CEO',exact:true})).toHaveCount(2,{timeout:15000});await w.getByRole('button',{name:'Submit this version to CEO',exact:true}).first().click();
 await page.goto(`${root}/boardroom`);w=workflow();await expect(w.locator('[data-workflow-task]')).toHaveCount(4,{timeout:15000});for(const task of await w.locator('[data-workflow-task]').all()){await task.getByText('Review exact saved submission',{exact:true}).click();await task.getByRole('button',{name:'Approve saved submission',exact:true}).click();await expect(task).toContainText('executed',{timeout:15000})}
 console.log('CHECKPOINT',page.url());checks.push('Boardroom request changes → Strategy revision → new exact submission → all four approvals/execution; prior versions retained.');
 await page.goto(`${root}/agents/finance`);w=workflow();await expect(w.getByRole('button',{name:'Use microphone',exact:true})).toBeVisible();await expect(w.locator('.workflow-conversation>article')).toHaveCount(1,{timeout:15000});const before=await w.locator('.workflow-conversation>article').count();await w.getByRole('button',{name:'Use microphone',exact:true}).click();await page.evaluate(()=>window.__speech.recognition.onresult({results:[[{transcript:'Can we spend $400 on a campaign?'}]]}));await expect(w.locator('.workflow-conversation>article')).toHaveCount(before);await w.getByRole('button',{name:'Finish dictation',exact:true}).click();await expect(w.getByLabel('Message Finance')).toHaveValue('Can we spend $400 on a campaign?');await expect(w.locator('.workflow-conversation>article')).toHaveCount(before);await w.getByRole('button',{name:'Send message',exact:true}).click();await expect(w.locator('.workflow-conversation>article')).toHaveCount(before+1,{timeout:15000});await expect(w.locator('.workflow-conversation>article').last()).toContainText('100.00');await w.getByRole('button',{name:'Stop audio',exact:true}).click();if(!(await page.evaluate(()=>window.__speech.cancelled>0)))throw Error('Audio not cancelled');
 await turn('What is a T?');await expect(w.locator('.workflow-conversation>article').last()).toContainText('T');await turn('Give me a pancake recipe');await expect(w.locator('.workflow-conversation>article').last()).toContainText(/business|simulator/i);
 await page.evaluate(()=>{delete window.SpeechRecognition});await w.getByRole('button',{name:'Use microphone',exact:true}).click();await expect(w.locator('.workflow-voice-state')).toContainText('unavailable');await turn('What is our saved launch deadline?');
 console.log('CHECKPOINT',page.url());checks.push('Voice mock: no auto-send, explicit Finish+Send, exact USD 100 gap, Stop playback, typed fallback; ambiguous and unrelated inputs.');
 // A response arriving after a newer edit must not clear it or start stale speech.
 await page.route('**/agents/finance',async route=>{if(route.request().method()==='POST')await new Promise(resolve=>setTimeout(resolve,700));await route.continue()});
 const savedCount=await w.locator('.workflow-conversation>article').count(),spokenCount=await page.evaluate(()=>window.__speech.spoken.length);
 await w.getByLabel('Message Finance').fill('Recommend a small launch option.');await w.getByRole('button',{name:'Send message',exact:true}).click();await w.getByLabel('Message Finance').fill('Keep this newer unsent question.');
 await expect(w.locator('.workflow-conversation>article')).toHaveCount(savedCount+1,{timeout:15000});await expect(w.getByLabel('Message Finance')).toHaveValue('Keep this newer unsent question.');if(await page.evaluate(()=>window.__speech.spoken.length)!==spokenCount)throw Error('Stale response started speech after a newer edit');
 await page.unroute('**/agents/finance');checks.push('Delayed response preserves newer typed input and does not start stale speech.');
 await mkdir('/tmp/workflow-browser',{recursive:true});await page.screenshot({path:'/tmp/workflow-browser/finance-desktop.png',fullPage:true});await page.setViewportSize({width:390,height:844});await page.screenshot({path:'/tmp/workflow-browser/finance-phone.png',fullPage:true});
 const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth+2);if(overflow)throw Error('Phone page overflows horizontally');
 await writeFile('/tmp/workflow-browser/result.json',JSON.stringify({checks,errors,businessId:bid,provider:'Mock model/image/speech, real routes/services/native auth; no live provider verification'},null,2));
 if(errors.length)throw Error('Browser errors: '+errors.join('; '));console.log(JSON.stringify({pass:true,checks,businessId:bid}));
}catch(error){await page.screenshot({path:'/tmp/shared-workflow-failure.png',fullPage:true});console.error(error);console.error(await page.locator('.workflow-alert').allTextContents());process.exitCode=1}finally{await browser.close()}
