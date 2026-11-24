// Public-only regression: no credentials, business creation or provider effects.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH||'/usr/bin/chromium',args:['--no-sandbox','--enable-unsafe-swiftshader']});
 try {
 const base=process.env.LANDING_BASE_URL||'http://127.0.0.1:3000';
 const shots=process.env.LANDING_SCREENSHOT_DIR||'/tmp/cinematic-landing';fs.mkdirSync(shots,{recursive:true});
 const errors=[],mutations=[];
 for(const colorScheme of ['dark','light']){
  const context=await browser.newContext({colorScheme,viewport:{width:1440,height:1000}});
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{if(!['GET','HEAD'].includes(r.method()))mutations.push(r.url())});
  await page.goto(base);await page.getByRole('button',{name:'Motion on',exact:true}).waitFor();
  await page.waitForFunction(()=>!document.querySelector('.launch-scene-status'));
  assert.equal(await page.locator('.launch-page').getAttribute('data-theme'),colorScheme);
  for(const width of [1440,1100,768,390,320]){
   await page.setViewportSize({width,height:1000});await page.waitForTimeout(120);await page.evaluate(()=>scrollTo(0,0));
   assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`horizontal overflow ${width}/${colorScheme}`);
   await page.screenshot({path:`${shots}/${colorScheme}-${width}.png`,fullPage:true});
  }
  await page.getByRole('button',{name:'Motion on',exact:true}).click();
  assert.equal(await page.locator('.launch-page').getAttribute('data-motion'),'off');
  // The canvas remains interactive and static with motion off.
  await page.getByRole('button',{name:'Finance',exact:true}).click();
  await page.getByRole('heading',{name:'Make the ambition add up.'}).waitFor();
  await page.reload();await page.getByRole('button',{name:'Motion off',exact:true}).waitFor();
  const toggle=page.getByRole('button',{name:`Switch to ${colorScheme==='dark'?'light':'dark'} mode`});await toggle.click();
  await page.reload();await page.waitForFunction(expected=>document.querySelector('.launch-page')?.dataset.theme===expected,colorScheme==='dark'?'light':'dark');
  await page.getByRole('link',{name:'Explore the free demo',exact:true}).click();assert.equal(new URL(page.url()).hash,'#demo');
  assert.equal(await page.getByRole('link',{name:'Create your free demo account',exact:true}).getAttribute('href'),base.includes('5173')?'/register':'/signup');
  await page.getByRole('button',{name:'See how it works',exact:true}).click();
  assert.ok(await page.locator('dialog').evaluate(e=>e.open));await page.keyboard.press('Escape');
  assert.ok(!await page.locator('dialog').evaluate(e=>e.open));
  await page.getByRole('link',{name:'Watch the demo & quick start',exact:true}).click();await page.waitForURL('**/getting-started');
  assert.equal(await page.locator('video source').getAttribute('src'),'/media/quick-start.mp4');
  await context.close();
 }
 const context=await browser.newContext({reducedMotion:'reduce',colorScheme:'dark'});const page=await context.newPage();
 await page.goto(base);await page.getByRole('button',{name:'Motion off',exact:true}).waitFor();assert.ok(await page.getByRole('button',{name:'Motion off',exact:true}).isDisabled());
 await page.emulateMedia({reducedMotion:'no-preference'});await page.getByRole('button',{name:'Motion on',exact:true}).waitFor();
 await page.emulateMedia({reducedMotion:'reduce'});await page.getByRole('button',{name:'Motion off',exact:true}).waitFor();
 await context.close();
 const fallback=await browser.newContext({colorScheme:'light'});
 await fallback.addInitScript(()=>{
  Object.defineProperty(window,'localStorage',{get(){throw new Error('Storage disabled')}});
  const original=HTMLCanvasElement.prototype.getContext;
  HTMLCanvasElement.prototype.getContext=function(kind,...args){return kind.startsWith('webgl')?null:original.call(this,kind,...args)};
  Object.defineProperty(window,'speechSynthesis',{value:undefined});
 });
 const f=await fallback.newPage();await f.goto(base);await f.getByText('3D is unavailable on this device.',{exact:false}).waitFor();
 await f.getByRole('button',{name:'HR',exact:true}).click();await f.getByRole('heading',{name:'Build the team behind the idea.'}).waitFor();
 await f.getByRole('button',{name:'Switch to dark mode'}).click();await f.getByRole('button',{name:'Motion on',exact:true}).click();
 await f.getByRole('button',{name:'Play introduction',exact:true}).click();await f.getByText('Voice unavailable here. Follow the captions.').waitFor();
 await f.getByRole('button',{name:'Close captions and pause tour'}).click();
 await f.screenshot({path:`${shots}/fallback.png`,fullPage:true});await fallback.close();
 assert.deepEqual(errors,[]);assert.deepEqual(mutations,[]);
 console.log('PASS: 10 theme/viewport combinations; persistent theme/motion; OS changes; agent selection; demo routes; dialog; WebGL/storage/voice fallbacks; no page errors or public mutations.');
 } finally { await browser.close() }
})().catch(e=>{console.error(e);process.exit(1)});
