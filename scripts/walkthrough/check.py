"""Public video playback checks; no real account or provider is accessed."""
from pathlib import Path
import httpx
from playwright.sync_api import sync_playwright,expect
root=Path(__file__).resolve().parents[2]/'.impeccable/review/walkthrough';root.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-gpu-compositing'])
 for app,url in [('next','http://localhost:3012'),('vite','http://127.0.0.1:5173')]:
  page=browser.new_page(viewport={'width':1280,'height':900});requests=[];errors=[]
  page.on('request',lambda r:requests.append(r.url));page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(url+'/getting-started');expect(page.get_by_role('heading',name='Your first plan, step by step.')).to_be_visible()
  page.wait_for_timeout(250);assert not any(r.endswith('.mp4') for r in requests),'MP4 eagerly downloaded'
  page.get_by_text('Watch the product demo',exact=True).click()
  video=page.locator('.quick-start video');video.evaluate('(v)=>v.play()')
  page.wait_for_function("document.querySelector('video').currentTime>0.2",timeout=20000)
  assert 50<video.evaluate('(v)=>v.duration')<100
  page.wait_for_function("document.querySelector('video').textTracks[0]?.cues?.length===8",timeout=10000)
  video.evaluate("(v)=>new Promise(resolve=>{v.addEventListener('seeked',()=>{v.pause();resolve()},{once:true});v.currentTime=25})")
  page.screenshot(path=str(root/f'{app}-desktop.png'),full_page=True)
  page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(root/f'{app}-mobile.png'),full_page=True)
  for width in [320,390,768,1280]:
   page.set_viewport_size({'width':width,'height':900});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(app,width)
  video.evaluate('(v)=>v.play()');page.get_by_text('Watch the product demo',exact=True).click();page.wait_for_timeout(100)
  assert video.evaluate('(v)=>v.paused'),'closing disclosure did not pause'
  assert not errors,errors
  response=httpx.get(url+'/media/quick-start.mp4',headers={'Range':'bytes=0-1023'})
  assert response.status_code==206,(app,response.status_code)
  assert len(response.content)==1024
  assert response.headers['content-type'].startswith('video/mp4')
  if app=='next':assert 'public' in response.headers.get('cache-control','')
  page.close()
 browser.close()
 print('PASS: both players; no eager MP4 request; native playback/seek; 8 caption cues; pause on close; 320–1280px; byte-range responses and public Next media cache.')
