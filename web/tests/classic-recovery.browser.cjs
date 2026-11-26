// Screenshots/API failures are synthetic. No private login, database, approval or money effect.
const {chromium}=require('playwright'),assert=require('node:assert/strict'),fs=require('node:fs');
const base=process.env.CLASSIC_BASE_URL||'http://127.0.0.1:5175';
(async()=>{const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--enable-unsafe-swiftshader']});try{
 const context=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'}),page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));let failedLookup=true,approvals=0;
 const business={id:'recovery-business',company_name:'Synthetic Recovery Startup',industry:'Software',starting_budget:10000,starting_headcount:5,enabled_agents:['ceo','finance','marketing','hr','operations']};
 const task={id:'budget-conflict',business_id:business.id,agent:'marketing',action_type:'campaign_launch',objective:'Synthetic campaign',payload:{campaign_name:'Synthetic campaign',requested_budget:29959.95},status:'pending_approval',approval_fingerprint:'exact-reviewed',ceo_review:{reason:'Requested funding exceeds current spendable funds; Finance must recheck.'}};
 await page.route('**/api/**',async route=>{const path=new URL(route.request().url()).pathname,method=route.request().method();if(!path.startsWith('/api/'))return route.continue();let data=[];
 if(path==='/api/auth/refresh')data={access_token:'fixture-token'};
 else if(path==='/api/auth/me')data={id:'fixture-owner',role:'owner'};
 else if(path==='/api/businesses'){if(failedLookup)return route.fulfill({status:503,json:{detail:'Synthetic database outage'}});data=[business]}
 else if(path.endsWith('/approve')){approvals++;assert.equal(route.request().postDataJSON().expected_fingerprint,'exact-reviewed');return route.fulfill({status:409,json:{detail:'Insufficient unreserved funds for this task'}})}
 else if(method!=='GET')throw Error('Unexpected mutation '+path);
 else if(path===`/api/businesses/${business.id}`)data=business;
 else if(path.endsWith('/agents'))data=Object.fromEntries(business.enabled_agents.map(role=>[role,{agent_name:role}]));
 else if(path.endsWith('/simulation/status'))data={is_running:false,is_paused:false,tick_count:20};
 else if(path.endsWith('/tasks'))data=[task];
 else if(path.endsWith('/history'))data=[1,2].map(day=>({timestamp:`2026-11-2${day}T12:00:00Z`,state:{budget_pool:10000,customer_base:20,brand_value:1}}));
 else if(path.endsWith('/finances'))data={cash:10000,reserved:0,available:10000,revenue:0,expenses:0,monthly_payroll_commitment:0};
 return route.fulfill({json:data})});
 await page.goto(base+`/b/${business.id}/dashboard`);await page.getByRole('heading',{name:'Your businesses could not load'}).waitFor({timeout:10000}).catch(async error=>{console.log(page.url(),(await page.locator('body').innerText()).slice(0,1500),errors);throw error});assert.ok(!page.url().includes('onboarding'));assert.equal(await page.getByText('Tell us about your company',{exact:true}).count(),0);
 failedLookup=false;await page.getByRole('button',{name:'Retry loading businesses'}).click();await page.getByRole('heading',{name:'Your startup at a glance.'}).waitFor();await page.getByRole('button',{name:'Approve',exact:true}).click();await page.getByRole('alert').filter({hasText:'Insufficient unreserved funds for this task'}).waitFor();assert.equal(approvals,1);assert.equal(await page.getByRole('button',{name:'Approve',exact:true}).count(),1);
 fs.mkdirSync('/tmp/classic-recovery',{recursive:true});
 async function contrast(selector){return page.locator(selector).first().evaluate(el=>{const rgb=value=>value.match(/[\d.]+/g).map(Number);const fg=rgb(getComputedStyle(el).color);let node=el,bg;while(node){const c=rgb(getComputedStyle(node).backgroundColor);if(c.length===3||c[3]>0){bg=c;break}node=node.parentElement}const base=rgb(getComputedStyle(document.body).backgroundColor);if(bg?.[3]<1)bg=bg.slice(0,3).map((v,i)=>v*bg[3]+base[i]*(1-bg[3]));const L=c=>c.slice(0,3).map(v=>v/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4).reduce((a,v,i)=>a+v*[.2126,.7152,.0722][i],0);return (Math.max(L(fg),L(bg))+.05)/(Math.min(L(fg),L(bg))+.05)})}
 for(const preset of ['glass','water','monolith'])for(const mode of ['light','dark'])for(const palette of ['emerald','champagne','lavender']){
 await page.locator('.appearance-control summary').click();await page.getByRole('radio',{name:new RegExp({glass:'Executive Glass',water:'Pearl Water',monolith:'Monolith'}[preset])}).check();await page.getByLabel('Color palette',{exact:true}).selectOption(palette);await page.getByLabel('Color mode',{exact:true}).selectOption(mode);await page.getByRole('button',{name:'Done',exact:true}).click();
 for(const selector of ['.hq-page-header h1','.hq-page-header p','.hq-kpi>span','.hq-kpi>strong','.hq-section-header h2','.hq-nav-link','.hq-brand strong','.hq-sidebar-footer button','.hq-review-section [role=alert]'])assert.ok(await contrast(selector)>=4.5,`Low contrast ${selector}: ${preset}/${mode}/${palette}`);
 for(const width of [1440,390]){await page.setViewportSize({width,height:1000});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));if(preset==='monolith'&&palette==='lavender'){await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:`/tmp/classic-recovery/${mode}-${width}.png`})}}
 }
 await page.reload();await page.getByRole('heading',{name:'Your startup at a glance.'}).waitFor();assert.equal(await page.getByRole('button',{name:'Approve',exact:true}).count(),1);assert.equal(approvals,1);assert.deepEqual(errors,[]);
 const login=await context.newPage();await login.route('http://localhost:3000/**',route=>route.fulfill({contentType:'text/html',body:'<h1>Mock main sign-in</h1>'}));await login.goto(base+'/login');await login.waitForURL('http://localhost:3000/login?next=*');assert.equal(await login.getByLabel('Password',{exact:true}).count(),0);
 console.log('PASS: failed lookup does not create/onboard; retry restores company; budget conflict remains visible with task intact; exact fingerprint; 18 appearance combinations at desktop/phone; persisted state; canonical login redirect. Fixtures only.');
 }finally{await browser.close()}})().catch(e=>{console.error(e);process.exit(1)});
