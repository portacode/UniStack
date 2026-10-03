from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import TestCase
from django.conf import settings
from unibot.models import Bot, Tool


class LocalBotTests(TestCase):
    def test_default_bot_uses_local_responses(self):
        namespace = {"request": object()}
        exec(Bot.get_default_code(), namespace)
        bot = SimpleNamespace(reply_using_llm=Mock(return_value="reply"))
        client_factory = Mock()
        with patch.dict(namespace, OpenAI=client_factory) as configured:
            result = configured["handle_incoming_message"](SimpleNamespace(platform="Email"), bot, [])
        self.assertEqual(result, "reply")
        options = bot.reply_using_llm.call_args.kwargs
        self.assertEqual(options["api_mode"], "responses")
        self.assertEqual(options["model_default"], settings.PORTACODE_LLM_MODEL)
        client_factory.assert_called_once_with(
            api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL
        )

    def test_upstream_tool_template_is_discoverable(self):
        self.assertIn("tool_definition", Tool.get_default_code())

    def test_webchat_default_streams_with_upstream_sink(self):
        namespace = {"request": object()}
        exec(Bot.get_default_code(), namespace)
        message = SimpleNamespace(platform="WebChat")
        bot = SimpleNamespace(reply_using_llm=Mock())
        with patch.dict(namespace, OpenAI=Mock(), WebChatMessageStreamSink=Mock()) as configured:
            configured["handle_incoming_message"](message, bot, [])
            configured["WebChatMessageStreamSink"].assert_called_once_with(message)
        options = bot.reply_using_llm.call_args.kwargs
        self.assertTrue(options["stream"])
        self.assertFalse(options["responses_options"]["store"])

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

    @patch('core.views.OpenAI')
    def test_demo_uses_local_responses(self, factory):
        self.client.force_login(self.user)
        factory.return_value.responses.create.return_value = SimpleNamespace(output_text='Hello')
        response = self.client.post('/api/ai/respond/', {'prompt': 'Hello'}, content_type='application/json')
        self.assertEqual(response.json()['response'], 'Hello')
        self.assertEqual(factory.call_args.kwargs['base_url'], settings.OPENAI_BASE_URL)
        self.assertFalse(factory.return_value.responses.create.call_args.kwargs['store'])

    def test_invalid_payload(self):
        self.client.force_login(self.user)
        for payload in ([], {}, {'prompt': 'x' * 8001}):
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
        self.assertIn('api_mode="responses"', bot.code)
        call_command("sync_unistack", verbosity=0)
        self.assertEqual(Bot.objects.filter(name="unistack").count(), 1)
        self.assertEqual(Channel.objects.filter(name="UniStack WebChat").count(), 1)
