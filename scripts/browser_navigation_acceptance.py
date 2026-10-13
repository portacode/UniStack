"""Check a fresh deployment using scripts.navigation_fixture settings."""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--url', default='http://127.0.0.1:8027')
parser.add_argument('--six-url')
parser.add_argument('--artifacts', type=Path, default=Path('/tmp/unistack-navigation-ui'))
args = parser.parse_args()
args.artifacts.mkdir(parents=True, exist_ok=True)
results = []
with sync_playwright() as p:
    browser = p.chromium.launch()
    for width in (360, 390, 430, 1440):
        context = browser.new_context(viewport={'width': width, 'height': 900})
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(args.url + '/assistant/')
        nav = page.locator('#site-navigation')
        nav.evaluate("el => el.dataset.persistent = 'yes'")
        baseline = nav.bounding_box()
        for path in ('/workspace/', '/workspace/library/', '/workspace/library/new/', '/preferences/', '/assistant/'):
            nav.locator(f'a[href="{path}"]').click()
            page.wait_for_url(lambda url: url.split('?')[0].endswith(path))
            expect(page.locator('#main-content')).not_to_have_attribute('aria-busy', 'true')
            expect(nav).to_have_attribute('data-persistent', 'yes')
            expect(nav.locator('a[aria-current=page]')).to_have_count(1)
            expect(nav.locator('a[aria-current=page]')).to_have_attribute('href', path)
            assert nav.bounding_box() == baseline
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            if path != '/assistant/':
                page.locator('#fixture-action').click()
                expect(page.locator('#fixture-count')).to_have_text('1')
                assert page.locator('.fixture-content').evaluate("el => getComputedStyle(el).display") == 'grid'
        expect(page.locator('#chat-loading')).to_be_hidden(timeout=60000)
        composer = page.locator('unicom-chat-with-sidebar textarea').first
        expect(composer).to_be_visible()
        if width <= 760:
            box = composer.bounding_box()
            assert box['y'] + box['height'] <= baseline['y']
            assert round(baseline['y'] + baseline['height']) == 900
            page.set_viewport_size({'width': width, 'height': 540})
            page.wait_for_timeout(300)  # Let the chat component settle its resize handler.
            box = composer.bounding_box()
            assert box['y'] + box['height'] <= nav.bounding_box()['y']
            page.set_viewport_size({'width': width, 'height': 900})
            page.wait_for_timeout(300)
            box = composer.bounding_box()
            assert box['y'] + box['height'] <= nav.bounding_box()['y']
            # Empty conversations intentionally center their composer; the chat
            # surface itself must still fill all space above the navigation.
            chat_box = page.locator('unicom-chat-with-sidebar').bounding_box()
            assert abs(chat_box['y'] + chat_box['height'] - nav.bounding_box()['y']) < 2
        page.screenshot(path=str(args.artifacts / f'chat-{width}.png'))
        nav.locator('a[href="/workspace/library/"]').click()
        page.wait_for_url('**/workspace/library/')
        page.locator('a[href="/materials/42/"]').click()
        page.wait_for_url('**/materials/42/')
        expect(nav.locator('a[aria-current=page]')).to_have_attribute('href', '/workspace/library/')
        page.go_back()
        page.wait_for_url('**/workspace/library/')
        page.go_forward()
        page.wait_for_url('**/materials/42/')
        page.reload()
        expect(nav.locator('a[aria-current=page]')).to_have_attribute('href', '/workspace/library/')
        page.locator('#fixture-action').click()
        expect(page.locator('#fixture-count')).to_have_text('1')
        page.screenshot(path=str(args.artifacts / f'product-{width}.png'))
        assert not errors, errors
        results.append({'width': width, 'shared_navigation': True, 'page_assets': True, 'history_and_reload': True})
        context.close()
    if args.six_url:
        page = browser.new_page(viewport={'width': 390, 'height': 844})
        page.goto(args.six_url + '/assistant/')
        expect(page.locator('#site-navigation')).to_be_hidden()
        page.locator('.menu-toggle').click()
        expect(page.locator('#site-navigation')).to_be_visible()
        expect(page.locator('#site-navigation a')).to_have_count(6)
        page.locator('#site-navigation a[href="/reports/"]').click()
        page.wait_for_url('**/reports/')
        expect(page.locator('#site-navigation')).to_be_hidden()
        page.locator('.menu-toggle').click()
        page.keyboard.press('Escape')
        expect(page.locator('#site-navigation')).to_be_hidden()
        results.append({'six_entries': 'mobile menu works on chat and product pages'})
    browser.close()
print(json.dumps(results))
