import os
import subprocess
import sys
import tempfile
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import Client, SimpleTestCase, TestCase, override_settings

from unicom.models import Account, AccountChat, Message, Request


@override_settings(UNISTACK_ALLOW_ANONYMOUS_CHAT=True)
class AnonymousChatTests(TestCase):
    def setUp(self):
        call_command("sync_unistack", verbosity=0)

    def send(self, client=None):
        response = (client or self.client).post(
            "/unicom/webchat/send/", {"text": "Guest hello"}, content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        result = response.json()
        return {"chat_id": result["chat_id"], "message_id": result["message"]["id"]}

    def test_guest_opens_chat_and_persists_request(self):
        self.assertContains(self.client.get("/"), "<unicom-chat-with-sidebar")
        sent = self.send()
        account_id = f"webchat_guest_{self.client.session.session_key}"
        queued = Request.objects.get(message_id=sent["message_id"])
        self.assertEqual(queued.account_id, account_id)
        self.assertEqual(queued.status, "QUEUED")
        messages = self.client.get("/unicom/webchat/messages/", {"chat_id": sent["chat_id"]})
        self.assertEqual(messages.json()["messages"][0]["text"], "Guest hello")
        self.assertEqual(self.client.get("/api/ai/usage/", {"chat_id": sent["chat_id"]}).status_code, 200)

    def test_guest_cannot_read_or_retry_another_session(self):
        sent = self.send()
        stranger = Client()
        self.assertEqual(stranger.get("/unicom/webchat/messages/", {"chat_id": sent["chat_id"]}).status_code, 404)
        self.assertEqual(stranger.get("/api/ai/usage/", {"chat_id": sent["chat_id"]}).status_code, 404)
        self.assertEqual(stranger.post("/api/ai/retry/", {"chat_id": sent["chat_id"]}, content_type="application/json").status_code, 404)

    def test_guest_requires_csrf_including_upstream_exempt_endpoints(self):
        client = Client(enforce_csrf_checks=True)
        for route in ("/unicom/webchat/send/", "/unicom/webchat/upload/", "/api/ai/respond/"):
            self.assertEqual(client.post(route, {"text": "hello"}).status_code, 403)
        client.get("/")
        response = client.post("/unicom/webchat/send/", {"text": "hello"}, content_type="application/json",
                               HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value)
        self.assertEqual(response.status_code, 200, response.content)

    def test_guest_ai_respond_queues_without_anonymous_user_foreign_key(self):
        response = self.client.post("/api/ai/respond/", {"prompt": "Hello"}, content_type="application/json")
        self.assertEqual(response.status_code, 202, response.content)
        self.assertIsNone(Message.objects.get(pk=response.json()["message_id"]).user_id)

    def test_real_login_transfers_history_after_session_rotation(self):
        sent = self.send()
        old_key = self.client.session.session_key
        user = get_user_model().objects.create_user("visitor", email="visitor@example.invalid", password="test-password", is_staff=True)
        response = self.client.post("/admin/login/?next=/", {"username": "visitor", "password": "test-password", "next": "/"})
        self.assertEqual(response.status_code, 302)
        self.assertNotEqual(self.client.session.session_key, old_key)
        self.assertFalse(Account.objects.filter(pk=f"webchat_guest_{old_key}").exists())
        self.assertTrue(AccountChat.objects.filter(chat_id=sent["chat_id"], account_id=f"webchat_user_{user.pk}").exists())
        self.assertEqual(Request.objects.get(message_id=sent["message_id"]).account_id, f"webchat_user_{user.pk}")
        self.assertEqual(self.client.get("/unicom/webchat/messages/", {"chat_id": sent["chat_id"]}).status_code, 200)
        self.assertEqual(self.client.get("/api/ai/usage/", {"chat_id": sent["chat_id"]}).status_code, 200)
        self.assertEqual(Client().get("/unicom/webchat/messages/", {"chat_id": sent["chat_id"]}).status_code, 404)

    def test_guest_attachment_is_private_to_own_session(self):
        with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            sent = self.send()
            message = Message.objects.get(pk=sent["message_id"])
            message.media.save("example.png", SimpleUploadedFile("example.png", b"attachment"))
            self.assertEqual(self.client.get(message.media.url).status_code, 200)
            self.assertEqual(Client().get(message.media.url).status_code, 404)
            other_user = get_user_model().objects.create_user("another")
            stranger = Client()
            stranger.force_login(other_user)
            self.assertEqual(stranger.get(message.media.url).status_code, 404)
            other_user.is_staff = True
            other_user.save(update_fields=["is_staff"])
            self.assertEqual(stranger.get(message.media.url).status_code, 200)

    def test_non_chat_media_remains_available_to_signed_in_users(self):
        with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            Path(media_root, "crm-file.txt").write_text("CRM document")
            self.assertEqual(self.client.get("/media/crm-file.txt").status_code, 404)
            self.client.force_login(get_user_model().objects.create_user("crm-reader"))
            self.assertEqual(self.client.get("/media/crm-file.txt").status_code, 200)

    @override_settings(UNISTACK_ALLOW_ANONYMOUS_CHAT=False)
    def test_disabled_policy_blocks_all_guest_entry_points(self):
        self.assertNotContains(self.client.get("/"), "<unicom-chat-with-sidebar")
        self.assertEqual(self.client.post("/unicom/webchat/send/").status_code, 401)
        self.assertEqual(self.client.get("/unicom/webchat/chats/").status_code, 401)
        self.assertEqual(self.client.post("/api/ai/respond/").status_code, 302)
        self.assertEqual(self.client.post("/api/ai/retry/").status_code, 302)
        self.assertEqual(self.client.get("/api/ai/usage/").status_code, 302)
        self.assertEqual(self.client.get("/media/media/example.png").status_code, 302)


class ChatInputBootstrapTests(SimpleTestCase):
    def test_boolean_values_and_redeployment_persistence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("UNISTACK_ALLOW_ANONYMOUS_CHAT=true\nOTHER=keep\n")
            env = dict(os.environ)
            env["UNISTACK_ALLOW_ANONYMOUS_CHAT"] = "false"
            command = [sys.executable, str(settings.BASE_DIR / "scripts/configure_env.py"), str(path)]
            subprocess.run(command, env=env, check=True, capture_output=True)
            self.assertIn("UNISTACK_ALLOW_ANONYMOUS_CHAT=false", path.read_text())
            env.pop("UNISTACK_ALLOW_ANONYMOUS_CHAT")
            subprocess.run(command, env=env, check=True, capture_output=True)
            self.assertIn("UNISTACK_ALLOW_ANONYMOUS_CHAT=false", path.read_text())
            self.assertIn("OTHER=keep", path.read_text())
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            env["UNISTACK_ALLOW_ANONYMOUS_CHAT"] = "True"
            subprocess.run(command, env=env, check=True, capture_output=True)
            self.assertIn("UNISTACK_ALLOW_ANONYMOUS_CHAT=true", path.read_text())
            env["UNISTACK_ALLOW_ANONYMOUS_CHAT"] = "invalid"
            result = subprocess.run(command, env=env, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
