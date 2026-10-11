// Project-owned visual theme for the pinned UniCom web components. Only CSS
// is attached to their open shadow roots; no component methods/data change.
// Keep this adapter scoped to the chat host and detach it on page navigation.
export function applyChatTheme(host) {
  const rules = `
    .unicom-chat-container { border:0; box-shadow:none; }
    @container(max-width:768px) {
      .sidebar-dismiss { left:auto; width:56px; }
      .sidebar-dismiss::after { content:'×'; position:absolute; right:10px; top:12px; width:36px; height:36px; line-height:32px; border-radius:50%; background:var(--unicom-background-color,#fff); color:var(--unicom-text-color,#202735); font-size:24px; }
    }
    .fa-spin, .retry-spinner { animation:none !important; }
    .loading-spinner { position:relative; display:flex; flex-direction:column; align-items:stretch; gap:12px; padding:24px; font-size:0; }
    .loading-spinner i { display:none; }
    .loading-spinner::before, .loading-spinner::after { content:''; display:block; height:44px; width:80%; border:0; border-radius:12px; background:linear-gradient(100deg,var(--unicom-message-bg-incoming,#f1f4f8) 20%,var(--unicom-border-color,#e4e8ef) 48%,var(--unicom-message-bg-incoming,#f1f4f8) 76%); background-size:240% 100%; animation:project-skeleton 1.8s ease-in-out infinite; }
    .loading-spinner::after { width:60%; }
    .fa-spinner { display:inline-block; width:24px; height:8px; border:0 !important; border-radius:4px; background:currentColor; opacity:.4; animation:project-pulse 1.5s ease-in-out infinite !important; }
    .fa-spinner::before { content:'' !important; }
    .retry-spinner { width:110px; height:12px; border:0; border-radius:6px; background:var(--unicom-border-color,#e4e8ef); animation:project-pulse 1.5s ease-in-out infinite !important; }
    @keyframes project-skeleton { from {background-position:100% 0} to {background-position:-100% 0} }
    @keyframes project-pulse { 50% {opacity:.2} }
    @media(prefers-reduced-motion:reduce) { .loading-spinner::before,.loading-spinner::after,.fa-spinner,.retry-spinner { animation:none !important; } }
  `;
  const roots = new Map();
  const sheet = new CSSStyleSheet();
  sheet.replaceSync(rules);
  const pending = new WeakSet();
  let disposed = false;
  function visit(node) {
    if (disposed) return;
    if (node.localName?.includes('-') && !node.shadowRoot && !pending.has(node)) {
      pending.add(node);
      customElements.whenDefined(node.localName).then(() => node.updateComplete).then(() => visit(node));
    }
    if (node.shadowRoot && !roots.has(node.shadowRoot)) {
      const root = node.shadowRoot;
      // Append after Lit's adopted sheets so project rules win the cascade.
      root.adoptedStyleSheets = [...root.adoptedStyleSheets, sheet];
      const observer = new MutationObserver(records => {
        for (const record of records) for (const added of record.addedNodes) {
          if (added.nodeType === 1) visit(added);
        }
        for (const [removed, watcher] of roots) {
          if (!removed.host.isConnected) {
            watcher.disconnect(); removed.adoptedStyleSheets = removed.adoptedStyleSheets.filter(item => item !== sheet); roots.delete(removed);
          }
        }
      });
      observer.observe(root, {childList:true, subtree:true});
      roots.set(root, observer);
      for (const child of root.querySelectorAll('*')) visit(child);
    }
    for (const child of node.children || []) visit(child);
  }
  visit(host);
  return () => {
    disposed = true;
    for (const [root, observer] of roots) {
      observer.disconnect(); root.adoptedStyleSheets = root.adoptedStyleSheets.filter(item => item !== sheet);
    }
    roots.clear();
  };
}
