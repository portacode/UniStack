// Progressive enhancement: every route still renders normally without JS.
let cleanup = () => {};
let pending;
let sequence = 0;
const status = document.getElementById('navigation-status');
const menu = document.querySelector('.menu-toggle');
const closeMenu = () => { document.querySelector('.site-sidebar').classList.remove('menu-open'); menu.setAttribute('aria-expanded', 'false'); };
menu.addEventListener('click', () => {
  const open = menu.getAttribute('aria-expanded') !== 'true';
  menu.setAttribute('aria-expanded', String(open));
  document.querySelector('.site-sidebar').classList.toggle('menu-open', open);
});
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && menu.getAttribute('aria-expanded') === 'true') {
    closeMenu(); menu.focus();
  }
});

async function mount(main) {
  if (!main.dataset.pageModule) return;
  try {
    const module = await import(main.dataset.pageModule);
    if (!main.isConnected) return;
    const unmount = await module.mount(main);
    if (!main.isConnected) unmount?.();
    else cleanup = unmount || (() => {});
  } catch {
    if (main.isConnected) status.textContent = 'This page could not finish loading. Reload to try again.';
  }
}

async function navigate(url, push = true) {
  pending?.abort();
  pending = new AbortController();
  const current = ++sequence;
  const oldMain = document.getElementById('main-content');
  oldMain.setAttribute('aria-busy', 'true');
  status.textContent = 'Loading…';
  closeMenu();
  try {
    const response = await fetch(url, {signal: pending.signal, headers: {'X-Requested-With': 'site-navigation'}});
    if (!response.ok || response.redirected) { location.assign(response.url || url); return; }
    const doc = new DOMParser().parseFromString(await response.text(), 'text/html');
    const next = doc.getElementById('main-content');
    if (!next) { location.assign(url); return; }
    if (current !== sequence) return;
    cleanup(); cleanup = () => {};
    oldMain.replaceWith(next);
    document.title = doc.title;
    document.getElementById('page-label').textContent = next.dataset.pageTitle || '';
    if (push) history.pushState({}, '', url);
    for (const link of document.querySelectorAll('#site-navigation a')) {
      if (new URL(link.href).pathname === location.pathname) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    }
    status.textContent = '';
    window.scrollTo(0, 0);
    next.focus({preventScroll: true});
    await mount(next);
  } catch (error) {
    if (error.name !== 'AbortError' && current === sequence) {
      oldMain.removeAttribute('aria-busy');
      status.textContent = 'Could not load the page. Check your connection and try again.';
      const retry = document.createElement('button');
      retry.className = 'button secondary'; retry.textContent = 'Try again';
      retry.addEventListener('click', () => navigate(url, push), {once: true});
      status.append(' ', retry);
    }
  }
}
document.addEventListener('click', event => {
  const link = event.target.closest('a[data-nav]');
  if (!link || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || link.target || link.download) return;
  const url = new URL(link.href);
  if (url.origin !== location.origin || url.hash) return;
  event.preventDefault();
  navigate(url.href);
});
window.addEventListener('popstate', () => navigate(location.href, false));
mount(document.getElementById('main-content'));
