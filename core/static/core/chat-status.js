const chat = document.querySelector('unicom-chat-with-sidebar');
const retry = document.getElementById('retry');
const usage = document.getElementById('usage');
const status = document.getElementById('chat-status');
const csrf = () => document.cookie.split('; ').find(value => value.startsWith('csrftoken='))?.split('=')[1] || '';
const activeChatId = () => chat.currentChatId || chat.selectedChatId;

retry.addEventListener('click', async () => {
  if (!activeChatId()) return;
  retry.disabled = true;
  try {
    const response = await fetch('/api/ai/retry/', {
      method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrf()},
      body: JSON.stringify({chat_id: activeChatId()}),
    });
    const result = await response.json();
    status.textContent = response.ok ? 'Reply queued for retry.' : result.error;
  } catch {
    status.textContent = 'Could not retry. Check your connection.';
  } finally {
    retry.disabled = false;
  }
});

usage.addEventListener('click', async () => {
  if (!activeChatId()) {
    status.textContent = 'Select a conversation to see its usage.';
    return;
  }
  try {
    const response = await fetch(`/api/ai/usage/?chat_id=${encodeURIComponent(activeChatId())}`);
    const result = await response.json();
    if (!response.ok) {
      status.textContent = result.error;
      return;
    }
    const totals = result.totals;
    status.textContent = `${totals.attempts} AI attempts · ${totals.input_tokens ?? 'unknown'} input tokens · ${totals.output_tokens ?? 'unknown'} output tokens. Charges appear in Portacode.`;
  } catch {
    status.textContent = 'Could not load usage.';
  }
});

setInterval(() => {
  const replies = (chat.messages || []).filter(message => message.is_outgoing);
  retry.hidden = replies.at(-1)?.stream_status !== 'failed';
}, 1000);
