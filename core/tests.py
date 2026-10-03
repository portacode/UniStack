from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import TestCase
from django.conf import settings
from unibot.models import Bot, Tool


class LocalBotTests(TestCase):
    def test_default_bot_uses_local_responses(self):
        namespace = {"request": object()}
        exec(Bot.get_default_code(), namespace)
        handler = Mock(return_value="reply")
        message, bot = object(), object()
        with patch.dict(namespace, reply=handler) as configured:
            result = configured["handle_incoming_message"](message, bot, [])
        self.assertEqual(result, "reply")
        handler.assert_called_once_with(message, bot, [], request=namespace["request"])

    def test_upstream_tool_template_is_discoverable(self):
        self.assertIn("tool_definition", Tool.get_default_code())

    def test_webchat_default_streams_with_upstream_sink(self):
        from core.integrations.bot import WebChatMessageStreamSink
        from unicom.services.webchat.streaming import WebChatMessageStreamSink as UpstreamSink
        self.assertIs(WebChatMessageStreamSink, UpstreamSink)

    def test_anonymous_ai_requires_login(self):
        self.assertEqual(self.client.post('/api/ai/respond/', {"prompt": "hello"}).status_code, 302)


class ReadinessTests(TestCase):
    def test_health(self):
        self.assertEqual(self.client.get('/health/').status_code, 200)


class DemoTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        self.user = get_user_model().objects.create_user(username='demo')

    def test_public_home_shows_sign_in(self):
        response = self.client.get('/')
        self.assertContains(response, 'Sign in to chat')
        self.assertNotContains(response, '<unicom-chat-with-sidebar')

    def test_signed_in_home_shows_form(self):
        self.client.force_login(self.user)
        self.assertContains(self.client.get('/'), '<unicom-chat-with-sidebar')

    def test_demo_queues_a_persisted_request(self):
        from django.core.management import call_command
        from unicom.models import Message, Request
        call_command("sync_unistack", verbosity=0)
        self.client.force_login(self.user)
        response = self.client.post('/api/ai/respond/', {'prompt': 'Hello'}, content_type='application/json')
        self.assertEqual(response.status_code, 202)
        message = Message.objects.get(pk=response.json()["message_id"])
        self.assertEqual(message.text, "Hello")
        self.assertEqual(Request.objects.get(message=message).status, "QUEUED")

    def test_invalid_payload(self):
        self.client.force_login(self.user)
        for payload in ([], {}, {'prompt': 'x' * 8001}, {'prompt': None}, {'prompt': []}, {'prompt': 'Hello', 'chat_id': []}):
            self.assertEqual(self.client.post('/api/ai/respond/', payload, content_type='application/json').status_code, 400)

    def test_demo_requires_csrf(self):
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post('/api/ai/respond/', {'prompt': 'Hello'}, content_type='application/json').status_code, 403)

    def test_webchat_requires_login(self):
        self.assertEqual(self.client.get('/unicom/webchat/chats/').status_code, 401)
        self.assertEqual(self.client.post('/unicom/webchat/send/').status_code, 401)

    def test_webchat_requires_csrf(self):
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post('/unicom/webchat/send/').status_code, 403)


class BootstrapTests(TestCase):
    def test_bootstrap_creates_ready_channel_and_bot_once(self):
        from django.core.management import call_command
        from unicom.models import Channel
        call_command("sync_unistack", verbosity=0)
        bot = Bot.objects.get(name="unistack")
        channel = Channel.objects.get(name="UniStack WebChat")
        self.assertTrue(channel.active)
        self.assertTrue(bot.request_category.is_public)
        self.assertTrue(bot.request_category.is_active)
        self.assertEqual(list(bot.request_category.allowed_channels.all()), [channel])
        self.assertIn('core.integrations.bot import reply', bot.code)
        call_command("sync_unistack", verbosity=0)
        self.assertEqual(Bot.objects.filter(name="unistack").count(), 1)
        self.assertEqual(Channel.objects.filter(name="UniStack WebChat").count(), 1)
