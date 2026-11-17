"""Public landing acceptance; voice callbacks are stubbed, no paid/audio provider."""
from pathlib import Path
import os
from playwright.sync_api import sync_playwright, expect
root=Path(__file__).resolve().parents[2]/'.impeccable/review/landing'
root.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=os.environ.get('STUDIO_CHROMIUM_PATH','/usr/bin/chromium'),headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-gpu-compositing'])
 for app,url,signup in [('next','http://localhost:3012','/signup'),('vite','http://127.0.0.1:5173','/register')]:
  context=browser.new_context(viewport={'width':1440,'height':1000},color_scheme='dark')
  context.add_init_script('''window.voiceCalls=[];window.SpeechSynthesisUtterance=class{constructor(text){this.text=text}};Object.defineProperty(window,'speechSynthesis',{value:{speaking:false,speak(u){this.speaking=true;window.voiceCalls.push(u);u.onstart?.()},cancel(){this.speaking=false}}});''')
  page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(url);expect(page.get_by_role('heading',level=1)).to_contain_text('Big ideas.')
  expect(page.locator('.launch-scene-status')).to_have_count(0,timeout=30000)
  assert page.evaluate('window.voiceCalls.length')==0,'audio started without a click'
  expect(page.get_by_role('link',name='Create your startup',exact=True).first).to_have_attribute('href',signup)
  for theme in ['dark','light']:
   if page.locator('.launch-page').get_attribute('data-theme')!=theme:page.get_by_role('button',name=f'Switch to {theme} mode').click()
   page.wait_for_timeout(350)
   for selector in ['.launch-steps','.launch-close','.launch-footer']:
    page.locator(selector).scroll_into_view_if_needed();page.wait_for_timeout(100)
   page.evaluate('scrollTo(0,0)');page.wait_for_timeout(150)
   expected='rgb(41, 27, 60)' if theme=='light' else 'rgb(248, 241, 255)'
   assert page.locator('.launch-hero h1').evaluate('(el)=>getComputedStyle(el).color')==expected,(app,theme,'headline color')
   page.screenshot(path=str(root/f'{app}-{theme}-desktop.png'),full_page=True,animations='disabled')
   page.set_viewport_size({'width':390,'height':844})
   for selector in ['.launch-steps','.launch-close','.launch-footer']:
    page.locator(selector).scroll_into_view_if_needed();page.wait_for_timeout(100)
   page.evaluate('scrollTo(0,0)');page.wait_for_timeout(150)
   page.screenshot(path=str(root/f'{app}-{theme}-mobile.png'),full_page=True,animations='disabled')
   for width in [320,390,768,1024,1440,1600]:
    page.set_viewport_size({'width':width,'height':1000});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(app,theme,width)
   page.set_viewport_size({'width':1440,'height':1000})
  page.reload();expect(page.locator('.launch-page')).to_have_attribute('data-theme','light')
  page.get_by_role('button',name='Meet the team',exact=True).click()
  for i,name in enumerate(['CEO','Finance','Marketing','HR','Operations']):
   expect(page.locator('.launch-live-caption strong')).to_have_text(name)
   page.wait_for_function('(i)=>window.voiceCalls.length===i+1',arg=i)
   assert page.evaluate('window.voiceCalls.at(-1).lang')=='en-US'
   page.evaluate('window.voiceCalls.at(-1).onend()')
  expect(page.locator('.launch-live-caption')).to_have_count(0)
  page.get_by_role('button',name='Play introduction',exact=True).click();expect(page.locator('.launch-live-caption')).to_be_visible()
  page.screenshot(path=str(root/f'{app}-tour.png'),full_page=True,animations='disabled')
  page.get_by_role('button',name='Switch to dark mode').click();page.wait_for_timeout(350)
  page.screenshot(path=str(root/f'{app}-tour-dark.png'),full_page=True,animations='disabled')
  page.get_by_role('button',name='Switch to light mode').click();page.wait_for_timeout(350)
  page.get_by_role('button',name='Pause introduction',exact=True).click();expect(page.locator('.launch-live-caption')).to_have_count(0)
  page.get_by_role('button',name='Next agent').click();expect(page.locator('.launch-intro-heading p')).to_have_text('CEO')
  page.get_by_role('button',name='See how it works').click();expect(page.get_by_role('dialog')).to_be_visible()
  page.screenshot(path=str(root/f'{app}-dialog.png'),full_page=False,animations='disabled')
  page.keyboard.press('Escape');expect(page.get_by_role('dialog')).not_to_be_visible()
  assert not errors,errors
  context.close()
 # Native unavailable speech and reduced-motion paths retain captions and selection.
 page=browser.new_page(viewport={'width':390,'height':844},color_scheme='light',reduced_motion='reduce')
 page.add_init_script("Object.defineProperty(window,'speechSynthesis',{value:undefined})")
 page.goto('http://localhost:3012');expect(page.locator('.launch-page')).to_have_attribute('data-theme','light')
 page.get_by_role('button',name='Meet the team',exact=True).click();expect(page.locator('.launch-live-caption')).to_be_visible()
 expect(page.locator('.launch-player>p')).to_contain_text('Voice unavailable')
 page.get_by_role('button',name='Close captions and pause tour').click()
 page.get_by_role('button',name='HR',exact=True).click();expect(page.locator('.launch-intro-heading p')).to_have_text('HR')
 page.emulate_media(color_scheme='dark');expect(page.locator('.launch-page')).to_have_attribute('data-theme','dark')
 expect(page.locator('meta[name="theme-color"]')).to_have_attribute('content','#100a1e')
 fallback=browser.new_page(viewport={'width':390,'height':844})
 fallback.add_init_script("HTMLCanvasElement.prototype.getContext=()=>null;Object.defineProperty(Storage.prototype,'getItem',{value(){throw new Error('storage disabled')}})")
 fallback.goto('http://localhost:3012');expect(fallback.locator('.launch-scene-status')).to_contain_text('3D is unavailable')
 fallback.get_by_role('button',name='Finance',exact=True).click();expect(fallback.locator('.launch-intro-heading p')).to_have_text('Finance')
 fallback.screenshot(path=str(root/'unavailable-3d.png'),full_page=True,animations='disabled')
 browser.close()
 print('PASS: both apps; theme/device preference/persistence; 320–1600px; no autoplay; all five English voice callbacks and captions; pause/wrap navigation; dialog Escape; reduced motion and unavailable speech.')
