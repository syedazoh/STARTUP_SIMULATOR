// All browser API calls are intercepted. Synthetic history, no real sessions/providers.
const {chromium}=require('playwright');const assert=require('node:assert/strict');const fs=require('node:fs');
(async()=>{const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});try{const page=await browser.newPage({viewport:{width:1440,height:1050}});const errors=[],writes=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/api/**',async route=>{const req=route.request(),url=new URL(req.url()),path=url.pathname;
  if(!path.startsWith('/api/'))return route.continue();
  if(path==='/api/auth/refresh')return route.fulfill({json:{access_token:'fixture-token'}});
  if(req.method()!=='GET'){writes.push(path);return route.fulfill({status:403,json:{detail:'Read-only synthetic browser fixture'}})}
  if(path==='/api/auth/me')return route.fulfill({json:{id:'fixture-owner',email:'fixture@example.com'}});
  if(path.endsWith('/simulation/status'))return route.fulfill({json:{is_running:false,is_paused:false,tick_count:12}});
  if(path.includes('simulation-runs'))return route.fulfill({json:[]});
  if(path.endsWith('/profile'))return route.fulfill({json:{}});
  if(path.endsWith('/history'))return route.fulfill({json:[5,4,3,2,1].map(i=>({state:{budget_pool:10000-i*200,customer_base:i*20,brand_value:i*5},synthetic:true}))});
  const response=await fetch('http://127.0.0.1:8012'+path+url.search);return route.fulfill({status:response.status,body:await response.text(),contentType:'application/json'});
 });
 await page.goto('http://127.0.0.1:5173/b/studio-business/dashboard');await page.getByRole('heading',{name:'Your startup at a glance.'}).waitFor({timeout:10000}).catch(async error=>{console.log(page.url(),(await page.locator('body').innerText()).slice(0,1500),errors);throw error});await page.locator('.recharts-line').first().waitFor();
 fs.mkdirSync('/tmp/dashboard-reference',{recursive:true});
 for(const width of [1440,1100,768,390,320]){await page.setViewportSize({width,height:1050});await page.evaluate(()=>scrollTo(0,0));await page.waitForTimeout(150);assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`overflow ${width}`);await page.screenshot({path:`/tmp/dashboard-reference/vite-${width}.png`,fullPage:true})}
 assert.deepEqual(errors,[]);assert.deepEqual(writes,[]);console.log('PASS: Vite dashboard charts with isolated synthetic API, 5 widths, no page errors or business writes.');
 }finally{await browser.close()}})().catch(e=>{console.error(e);process.exit(1)});
