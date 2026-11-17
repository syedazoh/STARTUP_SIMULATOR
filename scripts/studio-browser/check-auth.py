"""Next auth against disposable localhost identity; no real provider/account."""
from playwright.sync_api import sync_playwright,expect
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 for route in ['login','signup']:
  page=browser.new_page();page.goto('http://localhost:3013/'+route)
  expect(page.locator('p[role=alert]')).to_contain_text('web/.env.local')
  expect(page.locator('form')).to_have_count(0);page.close()
 page=browser.new_page();page.goto('http://localhost:3012/login')
 page.get_by_label('Email address').fill('wrong-fixture@example.com');page.get_by_label('Password',exact=True).fill('wrong-password')
 page.get_by_role('button',name='Sign in',exact=True).click();expect(page.locator('p[role=alert]')).to_contain_text('Sign-in failed')
 page.get_by_label('Email address').fill('studio-fixture@example.com');page.get_by_label('Password',exact=True).fill('fixture-password')
 page.get_by_role('button',name='Sign in',exact=True).click();page.wait_for_url('**/workspace')
 page.reload();expect(page.get_by_role('heading',name='Your businesses',exact=True)).to_be_visible()
 page.get_by_role('button',name='Sign out',exact=True).click();page.wait_for_url('**/login');page.goto('http://localhost:3012/workspace');page.wait_for_url('**/login');page.close()
 for email,confirmed in [('confirm-fixture@example.com',False),('immediate-fixture@example.com',True)]:
  page=browser.new_page();page.goto('http://localhost:3012/signup')
  page.get_by_label('Email address').fill(email);page.get_by_label('Password',exact=True).fill('fixture-password')
  page.get_by_role('button',name='Create account',exact=True).click()
  if confirmed:page.wait_for_url('**/workspace');expect(page.get_by_role('heading',name='Your businesses',exact=True)).to_be_visible()
  else:
   page.wait_for_url('**/login?notice=verify');expect(page.locator('p[role=status]')).to_contain_text('confirm your account')
   page.goto('http://localhost:3012/workspace');page.wait_for_url('**/login')
  page.close()
 page=browser.new_page();page.goto('http://localhost:3012/login');page.get_by_label('Email address').fill('unavailable-fixture@example.com');page.get_by_label('Password',exact=True).fill('fixture-password')
 page.get_by_role('button',name='Sign in',exact=True).click();expect(page.locator('p[role=alert]')).to_contain_text('Cannot reach the authentication provider')
 browser.close()
 print('PASS: missing-config guidance; wrong password; sign-in/reload; logout/protected redirect; signup with and without a session; unavailable-provider feedback. Local fixtures only.')
