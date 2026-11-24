// UI acceptance uses explicit local identity/mocked-Mongo fixture.
// Actual process/Mongo evidence is separately tested by backend integration tests.
const {chromium}=require('playwright');const assert=require('node:assert/strict');const fs=require('node:fs');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH,headless:true,args:['--no-sandbox']});
 try {
  const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:3000/login');await page.getByLabel('Email address').fill('distributed-browser@example.com');await page.getByLabel('Password',{exact:true}).fill('test-password');await page.getByRole('button',{name:'Sign in',exact:true}).click();await page.waitForURL('**/workspace');
  await page.getByText('Create a business',{exact:true}).click();await page.getByLabel('Company name').fill('Seven-role Browser Startup');await page.getByLabel('Industry',{exact:true}).fill('Software');await page.getByRole('button',{name:'Create workspace'}).click();await page.waitForURL(/workspace\/[\w-]+$/);
  await page.getByRole('link',{name:'Seven-role launch simulation & evidence →'}).click();await page.getByRole('heading',{name:'Seven-role launch simulation',exact:true}).waitFor();
  const url=page.url();await page.getByRole('button',{name:'Start synthetic analysis'}).click();await page.getByRole('heading',{name:'Launch analysis · ready for review'}).waitFor({timeout:30000});
  for(const role of ['CEO','MARKETING','FINANCE','HR','OPERATIONS','SUPPORT','STRATEGY'])await page.getByRole('heading',{name:role+' · succeeded',exact:true}).waitFor();
  await page.getByText('Thank you for your question. I cannot confirm the policy from authorized sources.',{exact:false}).waitFor();
  const downloadPromise=page.waitForEvent('download');await page.getByRole('link',{name:'Download evidence JSON'}).click();const download=await downloadPromise;
  const bundle=JSON.parse(fs.readFileSync(await download.path(),'utf8'));assert.equal(bundle.schema_version,1);assert.equal(bundle.records.filter(r=>r.record_type==='role_result').length,7);assert.equal(bundle.truncated,false);
  const csvPromise=page.waitForEvent('download');await page.getByRole('link',{name:'Download evidence CSV'}).click();const csv=await csvPromise;assert.ok(fs.readFileSync(await csv.path(),'utf8').startsWith('record_type,record_id,'));
  await page.getByRole('button',{name:'Create campaign for owner review'}).click();await page.getByText('Campaign: pending_approval',{exact:false}).waitFor();await page.getByRole('link',{name:'Review campaign in command center'}).click();
  await page.getByRole('button',{name:'Review owner decision'}).first().click();await page.getByRole('button',{name:'Approve and execute'}).click();await page.getByText('Approval processed.',{exact:false}).waitFor();await page.goto(url);await page.getByText('Campaign: executed',{exact:false}).waitFor();
  for(const width of [320,768,1440]){await page.setViewportSize({width,height:1000});assert.ok(await page.evaluate('document.documentElement.scrollWidth<=innerWidth'),`overflow ${width}`)}
  await page.screenshot({path:'/tmp/fyp-distributed-ui.png',fullPage:true});assert.deepEqual(errors,[]);
  console.log('Seven saved role outputs, abstention, JSON/CSV download, owner approval/execution/report, reload and mobile passed (local fixtures).');
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exit(1)});
