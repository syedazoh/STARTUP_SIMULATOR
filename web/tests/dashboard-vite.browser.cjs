// All browser API calls are intercepted. Synthetic history, no real sessions/providers.
const {chromium}=require('playwright');const assert=require('node:assert/strict');const fs=require('node:fs');
(async()=>{const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--enable-unsafe-swiftshader']});try{const page=await browser.newPage({viewport:{width:1440,height:1050}});let team=null;const errors=[],writes=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/api/**',async route=>{const req=route.request(),url=new URL(req.url()),path=url.pathname;
  if(!path.startsWith('/api/'))return route.continue();
  if(path==='/api/auth/refresh')return route.fulfill({json:{access_token:'fixture-token'}});
  if(req.method()==='PUT'&&path.endsWith('/workforce')){team=req.postDataJSON();writes.push(path);return route.fulfill({json:{workforce:team}})}
  if(req.method()==='GET'&&path==='/api/businesses/studio-business'&&team)return route.fulfill({json:{id:'studio-business',starting_headcount:7,workforce:team}});
  if(req.method()!=='GET'){writes.push(path);return route.fulfill({status:403,json:{detail:'Read-only synthetic browser fixture'}})}
  if(path==='/api/auth/me')return route.fulfill({json:{id:'fixture-owner',email:'fixture@example.com'}});
  if(path.endsWith('/simulation/status'))return route.fulfill({json:{is_running:false,is_paused:false,tick_count:12}});
  if(path.includes('simulation-runs'))return route.fulfill({json:[]});
  if(/\/agents\/(ceo|finance|marketing|hr|operations)$/.test(path))return route.fulfill({json:{agent_id:path.split('/').pop(),agent_name:path.split('/').pop(),decision_count:2}});
  if(path.endsWith('/finances'))return route.fulfill({json:{cash:10000,reserved:0,available:10000,revenue:0,expenses:0,monthly_payroll_commitment:0}});
  if(path.endsWith('/profile'))return route.fulfill({json:{}});
  if(path.endsWith('/history'))return route.fulfill({json:[5,4,3,2,1].map(i=>({state:{budget_pool:10000-i*200,customer_base:i*20,brand_value:i*5},synthetic:true}))});
  const response=await fetch('http://127.0.0.1:8012'+path+url.search);return route.fulfill({status:response.status,body:await response.text(),contentType:'application/json'});
 });
 await page.goto('http://127.0.0.1:5173/b/studio-business/dashboard');await page.getByRole('heading',{name:'Your startup at a glance.'}).waitFor({timeout:10000}).catch(async error=>{console.log(page.url(),(await page.locator('body').innerText()).slice(0,1500),errors);throw error});await page.locator('.recharts-line').first().waitFor();
 fs.mkdirSync('/tmp/dashboard-reference',{recursive:true});
 for(const width of [1440,1100,768,390,320]){await page.setViewportSize({width,height:1050});await page.evaluate(()=>scrollTo(0,0));await page.waitForTimeout(150);assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`overflow ${width}`);await page.screenshot({path:`/tmp/dashboard-reference/vite-${width}.png`,fullPage:true})}
 for(const [role,label] of [['finance','Finance'],['marketing','Marketing'],['hr','HR'],['operations','Operations'],['ceo','CEO']]){await page.goto(`http://127.0.0.1:5173/b/studio-business/agents/${role}`);await page.getByRole('heading',{name:`${label} Agent`,exact:true}).waitFor({timeout:10000}).catch(async error=>{console.log('Role failure',role,page.url(),(await page.locator('body').innerText()).slice(0,2000),errors);throw error});await page.locator('.agent-presence[data-scene=ready]').waitFor();assert.equal(await page.locator('.classic-workspace-footer').count(),1)}
 await page.setViewportSize({width:1440,height:600});assert.ok(await page.locator('.hq-sidebar nav').evaluate(e=>e.scrollHeight>e.clientHeight));await page.locator('.hq-sidebar nav').evaluate(e=>{e.scrollTop=e.scrollHeight});await page.locator('.hq-sidebar nav').getByRole('link',{name:'Operations',exact:true}).click();await page.getByRole('heading',{name:'Operations Agent',exact:true}).waitFor();
 await page.locator('.classic-workspace-footer').scrollIntoViewIfNeeded();await page.screenshot({path:'/tmp/dashboard-reference/classic-agent-footer.png'});
 await page.goto('http://127.0.0.1:5173/b/studio-business/profile');await page.getByText('Team setup · reported employee breakdown',{exact:true}).click();await page.getByLabel('Reported total employees').fill('7');
 await page.getByRole('button',{name:'Add department / role',exact:true}).click();await page.getByLabel('Role',{exact:true}).last().fill('Test analyst');await page.getByLabel('People',{exact:true}).last().fill('1');await page.getByRole('button',{name:'Save employee breakdown',exact:true}).click();await page.getByRole('status').filter({hasText:'Employee breakdown saved.'}).waitFor();assert.equal(team.positions.at(-1).role,'Test analyst');
 for(const mode of ['light','dark']){await page.locator('.appearance-control summary').click();await page.getByLabel('Color mode',{exact:true}).selectOption(mode);await page.getByRole('button',{name:'Done',exact:true}).click();for(const width of [1440,390,320]){await page.setViewportSize({width,height:1050});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`profile overflow ${mode}/${width}`);await page.screenshot({path:`/tmp/dashboard-reference/profile-${mode}-${width}.png`,fullPage:true})}}
 assert.deepEqual(errors,[]);assert.deepEqual(writes,['/api/businesses/studio-business/workforce']);console.log('PASS: classic dashboard and five agent pages, sidebar scrolling, isolated employee editing, light/dark profile at three widths; only the expected fake workforce write, no page errors.');
 }finally{await browser.close()}})().catch(e=>{console.error(e);process.exit(1)});
