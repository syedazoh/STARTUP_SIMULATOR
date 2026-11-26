// Disposable local provider, mocked database and offline model. No real accounts.
let diagnosticPage;
const {chromium}=require('playwright');const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const page=await browser.newPage();diagnosticPage=page;const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:3000/login?method=password');
 await page.getByLabel('Email address').fill('automation-browser@example.com');
 await page.getByLabel('Password',{exact:true}).fill('test-password');
 await page.getByRole('button',{name:'Sign in',exact:true}).click();await page.waitForURL('**/workspace');
 await page.getByText('Create a business',{exact:true}).click();
 await page.getByLabel('Company name').fill('Automation Browser Startup');
 await page.getByLabel('Industry',{exact:true}).fill('Software');
 await page.getByRole('button',{name:'Create workspace'}).click();await page.waitForURL(/workspace\/[\w-]+$/);
 await page.getByRole('button',{name:'Finance',exact:true}).click();await page.getByLabel('Requested amount',{exact:true}).fill('25');
 await page.getByRole('button',{name:'Submit proposal'}).click();await page.getByRole('button',{name:'Review owner decision'}).first().waitFor();
 await page.locator('a[href$="/automation"]').first().click();
 await page.getByRole('heading',{name:'Automation & knowledge',exact:true}).waitFor();
 await page.getByText('Worker: enabled',{exact:false}).waitFor();
 await page.getByRole('button',{name:'Queue task-status brief'}).click();
 await page.getByText(/succeeded, attempt/).first().waitFor({timeout:20000});
 const future=new Date(Date.now()+3600000),local=new Date(future.getTime()-future.getTimezoneOffset()*60000).toISOString().slice(0,16);
 await page.getByLabel('Task',{exact:true}).selectOption({index:1});await page.getByLabel('Due date & time').fill(local);
 await page.getByLabel('Reason',{exact:true}).fill('Browser acceptance commitment');await page.getByRole('button',{name:'Save deadline'}).click();await page.getByText('Saved.',{exact:true}).waitFor();
 await page.getByLabel('Document key').fill('launch-policy');await page.getByLabel('Title',{exact:true}).fill('Launch approval policy');
 await page.getByLabel('Document text').fill('# Launch\n\nCampaign approval requires signed owner review before publication.');
 await page.getByRole('button',{name:'Queue document indexing'}).click();await page.getByText(/Launch approval policy v1 — ready/).waitFor({timeout:20000});
 await page.getByLabel('Ask the documents').fill('campaign approval owner review');await page.getByLabel('Department',{exact:true}).selectOption('ceo');
 await page.getByRole('button',{name:'Answer with evidence'}).click();await page.getByText(/extractive_fallback/).waitFor();
 assert.match(await page.locator('body').innerText(),/Campaign approval requires signed owner review/);
 await page.getByRole('button',{name:'Create access token'}).click();const token=page.getByRole('textbox',{name:'MCP access token'});await token.waitFor();assert.match(await token.inputValue(),/^ey/);
 await page.getByRole('button',{name:'Hide token'}).click();assert.equal(await token.count(),0);
 await page.getByRole('button',{name:'Revoke access'}).first().click();await page.getByText(/revoked/).first().waitFor();
 for(const width of [320,390,768]){await page.setViewportSize({width,height:844});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false,`Automation overflows at ${width}px`);}
 await page.setViewportSize({width:390,height:844});
 const fs=require('node:fs');const dir=process.env.WORKSPACE_SCREENSHOT_DIR||'/tmp/workspace-screenshots';fs.mkdirSync(dir,{recursive:true});await page.screenshot({path:dir+'/automation-mobile.png',fullPage:true});
 assert.deepEqual(errors,[]);console.log('Automation acceptance passed: brief, deadline, indexing, citations, MCP revoke and mobile layout.');await browser.close();
})().catch(async e=>{if(diagnosticPage){const fs=require('node:fs');const dir=process.env.WORKSPACE_SCREENSHOT_DIR||'/tmp/workspace-screenshots';fs.mkdirSync(dir,{recursive:true});await diagnosticPage.screenshot({path:dir+'/automation-failure.png',fullPage:true}).catch(()=>{});fs.writeFileSync(dir+'/automation-failure.html',await diagnosticPage.content().catch(()=>''));}console.error(e);process.exit(1)});
