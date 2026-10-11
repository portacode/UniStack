"""Exercise the shared shell, loading states and responsive layouts without AI tokens."""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--url', default='http://127.0.0.1:8000')
parser.add_argument('--artifacts', type=Path, default=Path('/tmp/unistack-site'))
args = parser.parse_args()
args.artifacts.mkdir(parents=True, exist_ok=True)
checks = []
with sync_playwright() as p:
    browser = p.chromium.launch()
    errors = []
    context = browser.new_context(viewport={'width': 1440, 'height': 900})
    page = context.new_page()
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(args.url)
    assert not page.evaluate("performance.getEntriesByType('resource').some(r => r.name.includes('webchat-with-sidebar') || r.name.includes('cdn.jsdelivr.net'))")
    home_heading = page.locator('main h1').inner_text()
    page.screenshot(path=str(args.artifacts / 'home-desktop.png'), full_page=True)
    checks.append('marketing_and_lazy_chat')

    # Hold navigation and the initial module independently to inspect real skeletons.
    requests, modules = [], []
    page.route('**/assistant/', lambda route: requests.append(route))
    page.route('**/webchat-with-sidebar.js', lambda route: modules.append(route))
    page.locator('main a[href="/assistant/"][data-nav]').first.click()
    expect(page.locator('#page-skeleton')).to_be_visible()
    page.screenshot(path=str(args.artifacts / 'page-skeleton.png'))
    page.wait_for_timeout(100)
    requests.pop().continue_()
    page.unroute('**/assistant/')
    page.wait_for_url('**/assistant/')
    expect(page.locator('#chat-loading')).to_be_visible()
    page.screenshot(path=str(args.artifacts / 'chat-skeleton.png'))
    page.wait_for_timeout(200)
    modules.pop().continue_()
    page.unroute('**/webchat-with-sidebar.js')
    page.locator('textarea').wait_for(timeout=45000)
    expect(page.locator('#chat-loading')).to_be_hidden(timeout=45000)
    checks.append('navigation_and_chat_skeletons')
    assert page.locator('#site-navigation a[aria-current]').get_attribute('href') == '/assistant/'
    page.screenshot(path=str(args.artifacts / 'assistant-desktop.png'))
    frame = page.locator('.chat-frame').bounding_box()
    workspace = page.locator('.workspace').bounding_box()
    assert abs(frame['x'] - workspace['x']) < 2 and abs(frame['width'] - workspace['width']) < 2
    assert abs(frame['y'] + frame['height'] - 900) < 3
    page.go_back()
    page.get_by_role('heading', name=home_heading, exact=True).wait_for()
    page.go_forward()
    page.locator('textarea').wait_for()
    page.reload()
    page.locator('textarea').wait_for()
    checks.append('history_reload_and_full_height')

    # Verify spinner replacements across nested shadow roots, not just the wrapper.
    page.locator('textarea').fill('Loading-state visual check; do not send.')
    page.locator('unicom-chat-with-sidebar').evaluate('el => {el.sending = true;}')
    page.wait_for_timeout(250)
    animations = page.locator('unicom-chat-with-sidebar').evaluate("""el => {
      const found = [];
      function visit(root) {
        for (const node of root.querySelectorAll('*')) {
          if (node.matches('.fa-spinner,.retry-spinner')) found.push(getComputedStyle(node).animationName);
          if (node.shadowRoot) visit(node.shadowRoot);
        }
      }
      visit(el.shadowRoot); return found;
    }""")
    assert animations and all('spin' not in name for name in animations), animations
    page.locator('unicom-chat-with-sidebar').evaluate('el => {el.sending = false;}')
    page.locator('textarea').fill('')
    checks.append('nested_loading_theme')

    for width, height in [(390, 844), (320, 700)]:
        page.set_viewport_size({'width': width, 'height': height})
        page.wait_for_timeout(350)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        nav = page.get_by_role('navigation').bounding_box()
        frame = page.locator('.chat-frame').bounding_box()
        assert abs(nav['y'] + nav['height'] - height) < 3
        assert frame['y'] + frame['height'] <= nav['y'] + 2
        assert abs(frame['y'] + frame['height'] - nav['y']) < 3
        assert not page.get_by_role('button', name='Menu', exact=True).is_visible()
    page.set_viewport_size({'width': 390, 'height': 844})
    page.get_by_role('button', name='Open chat list', exact=True).click()
    page.get_by_role('button', name='Close chat list', exact=True).click()
    page.wait_for_timeout(350)
    page.screenshot(path=str(args.artifacts / 'assistant-mobile.png'))
    page.locator('#site-navigation a[href="/"]').click()
    page.get_by_role('heading', name=home_heading, exact=True).wait_for()
    page.screenshot(path=str(args.artifacts / 'home-mobile.png'), full_page=True)
    checks.append('mobile_bottom_tabs_and_chat_geometry')

    page.route('**/assistant/', lambda route: route.abort())
    page.locator('main a[href="/assistant/"][data-nav]').first.click()
    page.get_by_role('button', name='Try again', exact=True).wait_for()
    expect(page.locator('#page-skeleton')).to_be_hidden()
    page.unroute('**/assistant/')
    page.get_by_role('button', name='Try again', exact=True).click()
    page.locator('textarea').wait_for()
    checks.append('navigation_failure_retry')

    for width, height, suffix in [(1440, 900, 'desktop'), (390, 844, 'mobile')]:
        page.set_viewport_size({'width': width, 'height': height})
        for route in ('login', 'signup'):
            page.goto(args.url + '/accounts/' + route + '/')
            expect(page.get_by_label('Username', exact=True)).to_be_visible()
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.screenshot(path=str(args.artifacts / (route + '-' + suffix + '.png')), full_page=True)
    page.goto(args.url + '/accounts/login/')
    page.get_by_label('Username', exact=True).fill('nonexistent-smoke-user')
    page.get_by_label('Password', exact=True).fill('incorrect')
    page.get_by_role('button', name='Sign in', exact=True).click()
    page.get_by_role('alert').wait_for()
    checks.append('auth_layouts_and_validation')

    # Backend tests cover the entry-count rule. Render both boundary layouts here.
    for count in (5, 6):
        def entries(route):
            response = route.fetch()
            html = response.text()
            links = ''.join(f'<a href="/page-{i}/" data-nav><span>Page {i}</span></a>' for i in range(count))
            import re
            html = re.sub(r'(<nav id="site-navigation"[^>]*>).*?(</nav>)', lambda match: match[1] + links + match[2], html, flags=re.S)
            html = html.replace('class="mobile-tabs"', 'class="mobile-tabs"' if count == 5 else 'class="mobile-menu"')
            route.fulfill(response=response, body=html)
        page.route(args.url + '/', entries)
        page.goto(args.url + '/')
        if count == 5:
            assert page.get_by_role('navigation').is_visible()
            assert not page.get_by_role('button', name='Menu', exact=True).is_visible()
        else:
            page.get_by_role('button', name='Menu', exact=True).click()
            assert page.get_by_role('navigation').get_by_role('link').count() == 6
            page.screenshot(path=str(args.artifacts / 'mobile-six-item-menu.png'))
            page.keyboard.press('Escape')
            assert not page.get_by_role('navigation').is_visible()
            expect(page.get_by_role('button', name='Menu', exact=True)).to_be_focused()
        page.unroute(args.url + '/')
    checks.append('five_and_six_entry_navigation')

    page.emulate_media(reduced_motion='reduce')
    page.goto(args.url + '/')
    assert page.locator('.skeleton').first.evaluate("el=>getComputedStyle(el).animationName") == 'none'
    checks.append('reduced_motion')
    assert not errors, errors
    browser.close()
print(json.dumps({'checks': checks, 'console_errors': errors, 'artifacts': str(args.artifacts)}))
