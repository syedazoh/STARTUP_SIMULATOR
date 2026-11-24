const {chromium}=require('playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH||'/usr/bin/chromium',args:['--no-sandbox']});
 try{
  const page=await browser.newPage();
  await page.route('**/media/quick-start.mp4',route=>route.fulfill({status:404,body:'Missing recording'}));
  await page.goto(process.env.LANDING_BASE_URL||'http://127.0.0.1:3002');
  await page.getByRole('button',{name:'Watch the project video',exact:true}).click();
  await page.getByRole('alert').filter({hasText:'The video could not start.'}).waitFor();
  assert.equal(await page.getByRole('link',{name:'download the recording'}).getAttribute('href'),'/media/quick-start.mp4');
  await page.unroute('**/media/quick-start.mp4');
  await page.getByRole('button',{name:'Retry video',exact:true}).click();
  await page.waitForFunction(()=>{const v=document.querySelector('.launch-video-dialog video');return !v.paused&&v.currentTime>.2});
  await page.locator('.launch-video-error').waitFor({state:'hidden'});
  await page.locator('.launch-video-dialog video').evaluate(v=>{v.currentTime=30});
  await page.waitForFunction(()=>{const v=document.querySelector('.launch-video-dialog video');return v.currentTime>=30&&!v.seeking&&v.readyState>=2});
  await page.getByRole('button',{name:'Close project video',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('.launch-video-dialog video').paused);
  console.log('PASS: missing video gives retry/download; retry plays real recording; close pauses.');
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exit(1)});
