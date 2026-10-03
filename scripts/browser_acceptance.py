"""Live acceptance test; uses the local AI balance and a temporary test account."""

import argparse
import io
import json
import secrets
import subprocess
import time
import tempfile
from pathlib import Path

from playwright.sync_api import Error, sync_playwright
from PIL import Image

password = secrets.token_urlsafe(24)
username = "polished_smoke_" + secrets.token_hex(5)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--url", default="http://127.0.0.1:8000")
parser.add_argument("--artifacts", type=Path, default=Path(tempfile.mkdtemp(prefix="unistack-browser-")))
args = parser.parse_args()
args.artifacts.mkdir(parents=True, exist_ok=True)
root = Path(__file__).resolve().parent.parent


def django(code):
    result = subprocess.run(
        ["docker", "compose", "exec", "-T", "web", "python", "manage.py", "shell", "-c", code],
        check=True, capture_output=True, text=True, cwd=root,
    )
    return result.stdout


def observe(response):
    if "/unicom/webchat/messages/" in response.url and response.status == 200:
        try:
            messages = response.json().get("messages", [])
        except Error:
            return
        for message in messages:
            if message.get("is_outgoing"):
                streamed_texts.add(message.get("text", ""))
    if "/unicom/webchat/send/" in response.url:
        assert response.status == 200, response.text()
        sent.update(response.json())


streamed_texts = set()
sent = {}
try:
    django("from django.contrib.auth import get_user_model; get_user_model().objects.create_superuser(" + repr(username) + ", " + repr(username + "@example.invalid") + ", " + repr(password) + ")")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.on("response", observe)
        page.goto(args.url)
        page.get_by_role("link", name="Sign in to chat").click()
        page.get_by_label("Username:").fill(username)
        page.get_by_label("Password:").fill(password)
        page.get_by_role("button", name="Log in").click()
        page.locator("textarea").wait_for(timeout=30000)
        prompt = "Write a 200-word explanation of how a Django application, PostgreSQL, and a background AI worker work together. Finish with the exact phrase STREAMING DEMO VERIFIED."
        page.locator("textarea").fill(prompt)
        page.locator("textarea").press("Enter")
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            page.wait_for_timeout(250)
            if any("STREAMING DEMO VERIFIED" in text for text in streamed_texts):
                break
        assert any("STREAMING DEMO VERIFIED" in text for text in streamed_texts), {"sent": sent, "texts": list(streamed_texts)}
        assert len(streamed_texts) > 2, "No intermediate streaming updates observed"
        page.screenshot(path=str(args.artifacts / "desktop.png"), full_page=True)
        chat_id = sent["chat_id"]
        check = django("import json; from unicom.models import Message, Request; chat_id=" + repr(chat_id) + "; print(json.dumps({'requests':list(Request.objects.filter(message__chat_id=chat_id).values_list('status',flat=True)), 'replies':list(Message.objects.filter(chat_id=chat_id,is_outgoing=True).values('text','raw'))}))")
        data = json.loads(check.splitlines()[-1])
        assert data["requests"] == ["COMPLETED"], data
        assert len(data["replies"]) == 1, data
        assert data["replies"][0]["raw"]["stream"]["status"] == "finished", data
        usage = page.request.get(args.url + "/api/ai/usage/", params={"chat_id": chat_id})
        assert usage.ok, usage.text()
        ledger = usage.json()
        assert ledger["totals"]["attempts"] == 1, ledger
        assert ledger["attempts"][0]["status"] == "completed", ledger
        assert ledger["totals"]["input_tokens"] > 0 and ledger["totals"]["output_tokens"] > 0, ledger
        page.get_by_role("button", name="Usage", exact=True).click()
        page.wait_for_function("document.getElementById('chat-status').textContent.includes('input tokens')")
        page.reload()
        page.locator("textarea").wait_for()
        page.wait_for_function("document.querySelector('unicom-chat-with-sidebar').messages.some(message => message.text && message.text.includes('STREAMING DEMO VERIFIED'))")
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        page.screenshot(path=str(args.artifacts / "mobile.png"), full_page=True)
        image_bytes = io.BytesIO()
        Image.new("RGB", (64, 64), color="red").save(image_bytes, format="PNG")
        page.locator('input[type="file"]').set_input_files({"name": "red-square.png", "mimeType": "image/png", "buffer": image_bytes.getvalue()})
        page.wait_for_function("document.querySelector('unicom-chat-with-sidebar').stagedUploadToken && !document.querySelector('unicom-chat-with-sidebar').attachmentUploading")
        page.locator("textarea").fill("What color is the image? End your reply with IMAGE DEMO VERIFIED.")
        page.get_by_role("button", name="Send message", exact=True).click()
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            page.wait_for_timeout(250)
            if any("IMAGE DEMO VERIFIED" in text for text in streamed_texts):
                break
        assert any("IMAGE DEMO VERIFIED" in text and "red" in text.lower() for text in streamed_texts), list(streamed_texts)
        page.wait_for_function("document.querySelector('unicom-chat-with-sidebar').messages.filter(message => message.is_outgoing).at(-1)?.stream_status === 'finished'")
        ledger = page.request.get(args.url + "/api/ai/usage/", params={"chat_id": chat_id}).json()
        assert ledger["totals"]["attempts"] == 2 and all(attempt["status"] == "completed" for attempt in ledger["attempts"]), ledger
        page.remove_listener("response", observe)
        browser.close()
        print(json.dumps({"intermediate_reply_versions": len(streamed_texts), "request": "COMPLETED", "reconnect": "passed", "mobile": "passed", "image": "passed", "usage_attempts": ledger["totals"]["attempts"], "artifacts": str(args.artifacts)}))
finally:
    # Remove only the temporary account's data; retain screenshots outside the repo.
    django(f"""
from django.contrib.auth import get_user_model
from unicom.models import Account, AccountChat, Chat, Message
from core.models import ModelInvocation
user = get_user_model().objects.filter(username={username!r}).first()
if user:
    account_id = f'webchat_user_{{user.pk}}'
    chats = list(AccountChat.objects.filter(account_id=account_id).values_list('chat_id', flat=True))
    ModelInvocation.objects.filter(chat_id__in=chats).delete()
    Chat.objects.filter(pk__in=chats).delete()
    Message.objects.filter(user=user).update(user=None)
    Account.objects.filter(pk=account_id).delete()
    user.delete()
""")
