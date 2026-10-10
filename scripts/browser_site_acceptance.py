"""Exercise the shared shell without consuming AI tokens."""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--url', default='http://127.0.0.1:8000')
parser.add_argument('--artifacts', type=Path, default=Path('/tmp/unistack-site'))
args = parser.parse_args()
args.artifacts.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch()
    errors = []
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(args.url)
    assert page.title().endswith('Workspace')
    assert not page.evaluate("performance.getEntriesByType('resource').some(r => r.name.includes('webchat-with-sidebar') || r.name.includes('cdn.jsdelivr.net'))")
    page.screenshot(path=str(args.artifacts / 'overview-desktop.png'), full_page=True)
    page.get_by_role('link', name='Open assistant').click()
    page.wait_for_url('**/assistant/')
    page.locator('textarea').wait_for(timeout=45000)
    assert page.locator('#site-navigation a[aria-current]').inner_text().endswith('Assistant')
    page.screenshot(path=str(args.artifacts / 'assistant-desktop.png'), full_page=True)
    page.go_back()
    page.get_by_role('heading', name='Welcome.').wait_for()
    page.go_forward()
    page.locator('textarea').wait_for()
    page.reload()
    page.locator('textarea').wait_for()
    page.set_viewport_size({'width': 390, 'height': 844})
    page.wait_for_timeout(350)  # Let the upstream responsive drawer transition settle.
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.get_by_role('button', name='Open chat list', exact=True).click()
    page.get_by_role('button', name='Close chat list', exact=True).click()
    page.wait_for_timeout(350)
    page.screenshot(path=str(args.artifacts / 'assistant-mobile.png'), full_page=True)
    page.get_by_role('button', name='Menu', exact=True).click()
    assert page.get_by_role('button', name='Menu', exact=True).get_attribute('aria-expanded') == 'true'
    page.get_by_role('navigation').get_by_role('link', name='Overview').click()
    page.get_by_role('heading', name='Welcome.').wait_for()
    assert page.get_by_role('button', name='Menu', exact=True).get_attribute('aria-expanded') == 'false'
    page.screenshot(path=str(args.artifacts / 'overview-mobile.png'), full_page=True)
    # A failed enhanced request keeps the current page and offers a retry.
    page.route('**/assistant/', lambda route: route.abort())
    page.get_by_role('link', name='Open assistant').click()
    page.get_by_role('button', name='Try again', exact=True).wait_for()
    page.unroute('**/assistant/')
    page.get_by_role('button', name='Try again', exact=True).click()
    page.locator('textarea').wait_for()
    page.get_by_role('link', name='Sign in', exact=True).click()
    page.get_by_label('Username', exact=True).fill('nonexistent-smoke-user')
    page.get_by_label('Password', exact=True).fill('incorrect')
    page.get_by_role('button', name='Sign in', exact=True).click()
    page.get_by_role('alert').wait_for()
    page.screenshot(path=str(args.artifacts / 'login-mobile.png'), full_page=True)
    assert not errors, errors
    browser.close()
print(json.dumps({'navigation': 'passed', 'lazy_loading': 'passed', 'history': 'passed', 'mobile': 'passed', 'network_retry': 'passed', 'login_validation': 'passed', 'console_errors': errors, 'artifacts': str(args.artifacts)}))
