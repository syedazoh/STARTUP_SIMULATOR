from playwright.sync_api import sync_playwright,expect
from pathlib import Path
root=Path(__file__).resolve().parents[2] / ".impeccable/review"
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 page=browser.new_page(viewport={'width':1440,'height':1000})
 def intercept(route):
  url=route.request.url
  if '/api/auth/refresh' in url: return route.fulfill(json={'access_token':'fixture-token'})
  if '/api/auth/me' in url:return route.fulfill(json={'id':'fixture-owner','email':'fixture@example.com'})
  if '/simulation/status' in url:return route.fulfill(json={'is_running':False,'tick_count':0})
  if '/simulation/simulation-runs' in url:return route.fulfill(json=[])
  if '/profile' in url:return route.fulfill(json={})
  route.continue_()
 page.route('**/api/**',intercept)
 page.goto('http://127.0.0.1:5173/b/studio-business/boardroom')
 expect(page.get_by_role('heading',name='Inside the AI boardroom.')).to_be_visible(timeout=15000)
 page.get_by_role('button',name='HR only',exact=True).click() if page.get_by_role('button',name='HR only',exact=True).count() else page.locator('.immersive-room-roster').get_by_role('button',name='H HR',exact=True).click()
 expect(page.locator('.boardroom-projected-labels button:visible')).to_have_count(1)
 expect(page.locator('.boardroom-projected-labels button:visible')).to_have_attribute('data-agent','hr')
 page.screenshot(path=str(root/"legacy-single-agent.png"),full_page=True)
 page.get_by_role('button',name='All events',exact=True).click()
 expect(page.locator('.boardroom-projected-labels button:visible')).to_have_count(5)
 for path in ['dashboard','decision-log','profile']:
  page.goto('http://127.0.0.1:5173/b/studio-business/'+path)
  for width in [390,1440]:
   page.set_viewport_size({'width':width,'height':1000});page.wait_for_timeout(400)
   assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (path,width)
 page.goto('http://127.0.0.1:5173/b/studio-business/boardroom');page.set_viewport_size({'width':390,'height':900});page.wait_for_timeout(500)
 page.screenshot(path=str(root/"legacy-readable-mobile.png"),full_page=True)
 print('PASS Vite: selected avatar only, all-event restoration; dashboard/history/profile mobile and desktop overflow checks.')
 browser.close()
