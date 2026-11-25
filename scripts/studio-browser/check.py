from pathlib import Path
import os
import httpx
from playwright.sync_api import sync_playwright,expect
root=Path(__file__).resolve().parents[2] / '.impeccable/review'
root.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=os.environ.get('STUDIO_CHROMIUM_PATH'),headless=True,args=['--no-sandbox','--enable-webgl','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 page=browser.new_page(viewport={'width':1440,'height':1050},device_scale_factor=1)
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://localhost:3012/login?method=password')
 page.get_by_label('Email address').fill('studio-fixture@example.com');page.get_by_label('Password',exact=True).fill('fixture-password');page.get_by_role('button',name='Sign in',exact=True).click();page.wait_for_url('**/workspace')
 page.get_by_role('link',name='Enter executive studio').click();page.wait_for_url('**/boardroom')
 page.locator('.scene-labels.is-ready').wait_for(timeout=30000)
 expect(page.get_by_role('heading',name='Your team. In motion.')).to_be_visible()
 expect(page.locator('.studio-attention strong')).to_have_text('1')
 # Avatar click updates the real selected-agent panel.
 page.get_by_role('button',name='Select Finance',exact=True).click();expect(page.locator('.studio-selected h2')).to_contain_text('Finance')
 # The fallback preserves selection and a route back to WebGL.
 page.get_by_role('button',name='Team list',exact=True).click();expect(page.locator('.studio-accessible-team')).to_be_visible()
 page.locator('.studio-accessible-team').get_by_role('button',name='HR People & hiring').click();expect(page.locator('.studio-selected h2')).to_contain_text('HR')
 page.get_by_role('button',name='3D view',exact=True).click();page.locator('.scene-labels.is-ready').wait_for()
 page.locator('.studio-task summary').click()
 page.screenshot(path=str(root/'desktop-live.png'),full_page=True)
 page.locator('.studio-task summary').click()
 page.get_by_role('button',name='Preview a task handoff').click()
 expect(page.get_by_text('Visual preview · synthetic',exact=True).first).to_be_visible()
 page.wait_for_timeout(900)
 page.screenshot(path=str(root/'desktop.png'),full_page=True)
 # The illustrative meeting includes HR sending to Operations, not just CEO/Finance.
 expect(page.locator('.scene-transfer-card')).to_contain_text('Share the proposed staffing schedule',timeout=18000)
 expect(page.locator('.collaboration-strip [data-direction="sending"]')).to_contain_text('HR')
 expect(page.locator('.collaboration-strip [data-direction="receiving"]')).to_contain_text('Operations')
 page.screenshot(path=str(root/'hr-operations-preview.png'),full_page=True)
 # Screenshot once per class; same state and same scene at all target sizes.
 page.get_by_role('button',name='Enter immersive view').click()
 expect(page.get_by_role('dialog')).to_be_visible()
 page.get_by_role('button',name='Follow handoffs',exact=True).click();page.wait_for_timeout(350)
 page.screenshot(path=str(root/'immersive.png'),full_page=False)
 page.get_by_role('button',name='Stop following',exact=True).click()
 page.keyboard.press('Escape');expect(page.get_by_role('dialog')).to_have_count(0)
 page.get_by_role('button',name='Reset camera',exact=True).click()
 page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(250)
 page.screenshot(path=str(root/'mobile.png'),full_page=True)
 for width in (320,768,1024,1280,1600):
  page.set_viewport_size({'width':width,'height':900});page.wait_for_timeout(100)
  assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'),f'overflow at {width}'
 page.get_by_role('button',name='Exit visual preview').click()
 # All projected labels remain distinct through narrow viewports and orbit.
 for width in (320,390):
  page.set_viewport_size({'width':width,'height':900});page.wait_for_timeout(100)
  for dx in (-70,140,-70):
   box=page.locator('.scene-viewport canvas').bounding_box();x=box['x']+box['width']/2;y=box['y']+box['height']*.8
   page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+dx,y,steps=5);page.mouse.up();page.wait_for_timeout(80)
   overlap=page.locator('.scene-labels').evaluate('''node=>{const boxes=[...node.children].map(n=>({id:n.dataset.agent,r:n.getBoundingClientRect()}));return boxes.flatMap((a,i)=>boxes.slice(i+1).filter(b=>a.r.left<b.r.right&&a.r.right>b.r.left&&a.r.top<b.r.bottom&&a.r.bottom>b.r.top).map(b=>a.id+"/"+b.id))}''')
   assert not overlap,overlap
 page.set_viewport_size({'width':1440,'height':1050})
 # A new persisted CEO budget assignment must draw a CEO → Finance route.
 response=httpx.post('http://127.0.0.1:8012/__fixture__/delegate-budget');assert response.status_code==200
 expect(page.locator('.scene-transfer-card')).to_contain_text('FINANCE',timeout=15000)
 expect(page.locator('.scene-transfer-card')).to_contain_text('CEO')
 expect(page.locator('.scene-transfer-card')).to_contain_text('Review department budget')
 page.screenshot(path=str(root/'ceo-finance-handoff.png'),full_page=True)
 # All five new routed events in one snapshot must play in order.
 response=httpx.post('http://127.0.0.1:8012/__fixture__/collaborate');assert response.status_code==200
 for i,(sender,receiver) in enumerate([('ceo','marketing'),('marketing','finance'),('finance','operations'),('operations','hr'),('hr','ceo')]):
  expect(page.locator('.scene-transfer-card')).to_contain_text(f'Fixture handoff {i+1}: {sender} to {receiver}',timeout=15000)
  expect(page.locator('.collaboration-strip [data-direction="sending"]')).to_contain_text(sender,ignore_case=True)
  expect(page.locator('.collaboration-strip [data-direction="receiving"]')).to_contain_text(receiver,ignore_case=True)
 page.screenshot(path=str(root/'all-agent-handoffs.png'),full_page=True)
 # Persisted decision-log coordination also reaches the scene.
 response=httpx.post('http://127.0.0.1:8012/__fixture__/decision-coordination');assert response.status_code==200
 expect(page.locator('.scene-transfer-card')).to_contain_text('Review staffing budget from decision log',timeout=15000)
 page.get_by_role('button',name='HR only',exact=True).click()
 expect(page.locator('.scene-labels button:visible')).to_have_count(1)
 expect(page.locator('.scene-labels button:visible')).to_have_attribute('data-agent','hr')
 page.screenshot(path=str(root/'single-agent-focus.png'),full_page=True)
 page.get_by_role('button',name='All events',exact=True).click()
 expect(page.locator('.scene-labels button:visible')).to_have_count(5)
 # Real decisions require opening exact payload; no preview action can approve.
 page.locator('.studio-task summary').click();expect(page.get_by_text('Product launch',exact=False).first).to_be_visible()
 page.get_by_role('button',name='Approve action',exact=True).click()
 expect(page.get_by_text('Decision saved. The backend result is shown below.')).to_be_visible()
 expect(page.locator('.studio-attention strong')).to_have_text('0')
 # A later task transition is drawn as owner → Marketing, not CEO approval.
 expect(page.locator('.scene-bottomline')).to_contain_text('OWNER',timeout=10000)
 page.reload();page.locator('.scene-labels.is-ready').wait_for();expect(page.locator('.scene-bottomline')).to_contain_text('Select an avatar')
 assert not errors,errors
 # Reduced motion still creates a real WebGL render and usable controls.
 reduced=browser.new_page(viewport={'width':1024,'height':900},reduced_motion='reduce')
 reduced.goto('http://localhost:3012/login?method=password');reduced.get_by_label('Email address').fill('studio-fixture@example.com');reduced.get_by_label('Password',exact=True).fill('fixture-password');reduced.get_by_role('button',name='Sign in',exact=True).click();reduced.wait_for_url('**/workspace');reduced.get_by_role('link',name='Enter executive studio').click();reduced.locator('.scene-labels.is-ready').wait_for()
 reduced_canvas=reduced.locator('.scene-viewport canvas')
 before=reduced_canvas.screenshot()
 reduced.get_by_role('button',name='Preview a task handoff').click();reduced.wait_for_timeout(150)
 during=reduced_canvas.screenshot();assert during!=before,'preview packet did not render'
 reduced.get_by_role('button',name='Exit visual preview').click();reduced.wait_for_timeout(150)
 after=reduced_canvas.screenshot();assert after==before,'synthetic packet remained after exit under reduced motion'
 print('PASS: exact reduced-motion canvas restored after exiting preview; immersive/follow/Escape and mobile label collision checks.')
 print('PASS: real WebGL; avatar selection; list fallback; preview; synthetic approval; owner handoff; no historical replay; 320–1600px overflow; reduced motion; no page errors.')
 browser.close()
