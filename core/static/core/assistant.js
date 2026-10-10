export async function mount(main) {
  const chat = main.querySelector('unicom-chat-with-sidebar');
  if (!chat) return;
  const loading = main.querySelector('#chat-loading');
  try {
    await import(chat.dataset.source);
    await customElements.whenDefined('unicom-chat-with-sidebar');
    if (!main.isConnected) return;
    loading.hidden = true;
  } catch {
    loading.textContent = 'The assistant could not load. Check your connection and try again.';
    const retry = document.createElement('button');
    retry.className = 'button secondary'; retry.textContent = 'Reload assistant';
    retry.addEventListener('click', () => location.reload()); loading.append(retry);
    return;
  }
  const {mountStatus} = await import('./chat-status.js');
  if (main.isConnected) return mountStatus(main);
}
