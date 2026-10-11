export async function mount(main) {
  const chat = main.querySelector('unicom-chat-with-sidebar');
  if (!chat) return;
  const loading = main.querySelector('#chat-loading');
  try {
    await import(chat.dataset.source);
    await customElements.whenDefined('unicom-chat-with-sidebar');
    if (!main.isConnected) return;
    await chat.updateComplete;
  } catch {
    loading.classList.add('chat-load-error');
    loading.textContent = 'The assistant could not load. Check your connection and try again.';
    const retry = document.createElement('button');
    retry.className = 'button secondary'; retry.textContent = 'Reload assistant';
    retry.addEventListener('click', () => location.reload()); loading.append(retry);
    return;
  }
  const {applyChatTheme} = await import('./chat-theme.js');
  if (!main.isConnected) return;
  const removeTheme = applyChatTheme(chat);
  const updateLoading = () => {
    loading.hidden = !chat.loading && !chat.loadingChats;
    chat.setAttribute('aria-busy', String(!loading.hidden));
  };
  updateLoading();
  const loadingTimer = setInterval(updateLoading, 100);
  const {mountStatus} = await import('./chat-status.js');
  const unmountStatus = main.isConnected ? mountStatus(main) : () => {};
  const cleanup = () => { clearInterval(loadingTimer); removeTheme(); unmountStatus(); };
  if (!main.isConnected) cleanup();
  else return cleanup;
}
