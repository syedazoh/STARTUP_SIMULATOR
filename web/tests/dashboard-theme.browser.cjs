// Local fake provider/API only. Never use with production credentials.
const {chromium}=require('playwright');const assert=require('node:assert/strict');const fs=require('node:fs');
(async()=>{const browser=await chromium.launch({executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH||'/usr/bin/chromium',args:['--no-sandbox']});try{
 const page=await browser.newPage({viewport:{width:1440,height:1050}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
 const base=process.env.DASHBOARD_BASE_URL||'http://localhost:3012';const shots='/tmp/dashboard-reference';fs.mkdirSync(shots,{recursive:true});
 await page.goto(base+'/login?method=password');await page.getByLabel('Email address').fill('studio-fixture@example.com');await page.getByLabel('Password',{exact:true}).fill('fixture-password');await page.getByRole('button',{name:'Sign in',exact:true}).click();await page.waitForURL('**/workspace');await page.goto(base+'/workspace/studio-business');
 await page.getByRole('heading',{name:'Orbit Studio · test fixture',exact:true}).waitFor();
 assert.equal(await page.locator('.overview-bars').count(),2);
 assert.match(await page.locator('.overview-bars[aria-label="Recorded financial snapshot"]').innerText(),/10,000/);
 const before=await(await fetch('http://127.0.0.1:8012/api/tasks/launch-fixture')).json();assert.equal(before.status,'pending_approval');
 await page.getByRole('button',{name:'Finance',exact:true}).click();await page.getByLabel('Requested amount',{exact:true}).waitFor();
 await page.getByRole('link',{name:'Open approval inbox',exact:true}).click();await page.getByRole('heading',{name:'Tasks and approvals',exact:true}).waitFor();
 assert.equal(new URL(page.url()).hash,'#tasks');
 const after=await(await fetch('http://127.0.0.1:8012/api/tasks/launch-fixture')).json();assert.equal(after.status,'pending_approval');
 for(const width of [1440,1100,768,390,320]){await page.setViewportSize({width,height:1050});await page.evaluate(()=>scrollTo(0,0));await page.waitForTimeout(120);assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`overflow ${width}`);await page.screenshot({path:`${shots}/next-${width}.png`,fullPage:true})}
 await page.getByRole('button',{name:'Review owner decision',exact:true}).click();await page.getByRole('button',{name:'Approve and execute',exact:true}).click();await page.getByText('Approval processed. Read the saved result;', {exact:false}).waitFor();
 assert.equal((await(await fetch('http://127.0.0.1:8012/api/tasks/launch-fixture')).json()).status,'executed');
 assert.deepEqual(errors,[]);console.log('PASS: saved snapshot charts, department form, inbox restores all tasks without authorizing, exact-action approval, 5 widths and no page errors.');
 }finally{await browser.close()}})().catch(e=>{console.error(e);process.exit(1)});
