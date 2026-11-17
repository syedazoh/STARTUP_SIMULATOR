"""Record the actual Next UI against the disposable localhost fixture only."""
from pathlib import Path
from time import monotonic
import json
from playwright.sync_api import sync_playwright,expect
OUT=Path('/tmp/startup-walkthrough');OUT.mkdir(exist_ok=True)
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-gpu-compositing'])
 auth=browser.new_context();login=auth.new_page();login.goto('http://localhost:3012/login')
 login.get_by_label('Email address').fill('studio-fixture@example.com');login.get_by_label('Password',exact=True).fill('fixture-password');login.get_by_role('button',name='Sign in',exact=True).click();login.wait_for_url('**/workspace');state=auth.storage_state();auth.close()
 context=browser.new_context(storage_state=state,viewport={'width':1280,'height':800},record_video_dir=str(OUT),record_video_size={'width':1280,'height':800},reduced_motion='reduce')
 page=context.new_page();start=monotonic();chapters=[]
 def chapter(title,caption,seconds=7):
  chapters.append({'start':round(monotonic()-start,3),'title':title,'caption':caption})
  page.evaluate('''title=>{let badge=document.getElementById('demo-badge');if(!badge){badge=document.createElement('div');badge.id='demo-badge';badge.style='position:fixed;right:12px;top:10px;padding:8px 13px;background:#e6d6ba;color:#291b3c;font:600 13px system-ui;border-radius:8px;z-index:99999;pointer-events:none';document.body.append(badge)}badge.textContent='PRODUCT DEMO · SYNTHETIC DATA';let note=document.getElementById('demo-chapter');if(!note){note=document.createElement('div');note.id='demo-chapter';note.style='position:fixed;inset:auto 0 0;padding:16px 28px;background:#10091df2;border-top:1px solid #896ba1;color:#f5eaff;font:600 20px system-ui;z-index:99999;pointer-events:none';document.body.append(note)}note.textContent=title}''',title)
  page.wait_for_timeout(seconds*1000)
 page.goto('http://localhost:3012/workspace');page.evaluate('scrollTo(0,0)')
 chapter('1 · Start in your workspace','Create an account or sign in, then create a business. This recording uses a disposable local demo identity.')
 page.get_by_text('Create a business',exact=True).click();page.get_by_label('Company name',exact=True).fill('Orbit Studio · synthetic demo');page.get_by_label('Industry',exact=True).fill('Software');page.get_by_label('Company name',exact=True).scroll_into_view_if_needed()
 chapter('2 · Create your company','Enter your company name, industry and simulated starting resources. Complete your business profile before planning.')
 page.get_by_role('button',name='Create workspace',exact=True).click();page.wait_for_url('**/workspace/studio-business');page.get_by_label('Business goal',exact=True).fill('Prepare a product launch within a simulated budget of 1000. Review costs and request owner approval before execution.')
 page.get_by_label('Business goal',exact=True).scroll_into_view_if_needed()
 chapter('3 · Give the CEO a concrete goal','Describe the outcome, budget and constraints. Generate a draft plan; do not activate it before reviewing the assignments.')
 page.get_by_role('button',name='Generate draft plan',exact=True).click();expect(page.get_by_text('CEO plan saved. Review its assignments before activation.')).to_be_visible(timeout=15000)
 page.get_by_text('Review 1 assignments',exact=True).click();page.get_by_text('Review 1 assignments',exact=True).evaluate("el=>el.scrollIntoView({block:'center'})")
 chapter('4 · Inspect assignments, then activate','Review the department, objective, exact payload and success criteria. Activation may run eligible work under existing policies.')
 page.get_by_role('button',name='Review activation',exact=True).click();page.get_by_role('button',name='Confirm activation',exact=True).click();expect(page.get_by_text('Plan activation processed. Check individual task statuses for progress and blockers.')).to_be_visible(timeout=15000)
 page.goto('http://localhost:3012/workspace/studio-business/boardroom');page.locator('.scene-labels.is-ready').wait_for(timeout=30000);page.evaluate('scrollTo(0,0)')
 chapter('5 · Open the executive studio','Inspect the five departments and recorded work. The boardroom visualizes actual saved records; its preview is illustrative.')
 page.locator('.studio-task summary').click();page.locator('.studio-task summary').evaluate("el=>el.scrollIntoView({block:'center'})")
 chapter('6 · Review the exact action','Check the task payload and simulation/live mode. Owner approval is separate from CEO review and can execute an eligible action.')
 page.get_by_role('button',name='Approve action',exact=True).click();expect(page.get_by_text('Decision saved. The backend result is shown below.')).to_be_visible(timeout=15000)
 expect(page.locator('.scene-bottomline')).to_contain_text('OWNER',timeout=15000);page.locator('.scene-bottomline').scroll_into_view_if_needed()
 chapter('7 · Follow the handoff and result','The owner decision returns to the department. The saved status refreshes; this demo result is simulated, not a real publication.')
 page.goto('http://localhost:3012/workspace/studio-business');page.get_by_role('heading',name='Department reports to the CEO').scroll_into_view_if_needed()
 chapter('8 · Check history and available reports','Read task status, decision history and available reports. Executed is different from delivered or verified complete. Connect external accounts only after setup and permission checks.',9)
 video=page.video;context.close();video.save_as(str(OUT/'quick-start.webm'));browser.close()
 chapters[0]['start']=0
 (OUT/'chapters.json').write_text(json.dumps(chapters,indent=2))
 print('Saved synthetic UI recording and chapter timings in /tmp/startup-walkthrough')
