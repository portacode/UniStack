import importlib.util
import os
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command, CommandError
from django.test import SimpleTestCase, TestCase
from unibot.models import Bot, Tool
from unicom.models import Message, Request, ToolCall

from core.integrations.bot import reply
from core.models import ModelInvocation


def event(event_type, **data):
    data = {"type": event_type, **data}
    return SimpleNamespace(**data, model_dump=lambda: data)


def completed_response(text="Hello", output=None):
    return {
        "id": "resp_" + uuid.uuid4().hex, "status": "completed", "output_text": text,
        "output": output or [], "usage": {
            "input_tokens": 12, "output_tokens": 8, "total_tokens": 20,
            "input_tokens_details": {"cached_tokens": 3},
            "output_tokens_details": {"reasoning_tokens": 2},
        },
    }


def successful_events(response=None):
    response = response or completed_response()
    return iter([
        event("response.created", response={"id": response["id"], "status": "in_progress"}),
        event("response.output_text.delta", delta="Hel"),
        event("response.output_text.delta", delta="lo"),
        event("response.completed", response=response),
    ])


class ModelFlowTests(TestCase):
    def setUp(self):
        call_command("sync_unistack", verbosity=0)
        self.bot = Bot.objects.get(name="unistack")
        self.user = get_user_model().objects.create_user("model_flow", email="model-flow@example.invalid")
        self.client.force_login(self.user)
        queued = self.client.post("/api/ai/respond/", {"prompt": "Hello"}, content_type="application/json")
        self.message = Message.objects.get(pk=queued.json()["message_id"])
        self.request = Request.objects.get(message=self.message)
        self.api = Mock()

    def process(self):
        with patch("core.integrations.bot.local_client", return_value=self.api):
            return self.bot.process_request(self.request)

    def test_completion_records_usage_and_one_reply(self):
        self.api.responses.create.return_value = successful_events()
        self.assertTrue(self.process())
        attempt = ModelInvocation.objects.get()
        self.assertEqual(attempt.status, "completed")
        self.assertEqual((attempt.input_tokens, attempt.output_tokens), (12, 8))
        self.assertEqual((attempt.cached_input_tokens, attempt.reasoning_tokens), (3, 2))
        self.assertEqual(attempt.request_id, self.request.pk)
        outgoing = Message.objects.get(chat=self.message.chat, is_outgoing=True)
        self.assertEqual(outgoing.text, "Hello")
        self.assertEqual(outgoing.raw["stream"]["status"], "finished")
        self.assertEqual(outgoing.raw["ai"]["invocation_id"], str(attempt.pk))
        self.request.refresh_from_db()
        self.assertEqual((self.request.llm_calls_count, self.request.llm_token_usage), (1, 20))
        self.assertFalse(self.api.responses.create.call_args.kwargs["store"])
        self.api.close.assert_called_once()
        attempt.error = "edited"
        with self.assertRaisesRegex(ValueError, "immutable"):
            attempt.save()

    def test_truncated_stream_retains_partial_text_and_can_retry(self):
        self.api.responses.create.return_value = iter([event("response.output_text.delta", delta="Partial")])
        self.assertFalse(self.process())
        attempt = ModelInvocation.objects.get()
        self.assertEqual(attempt.status, "failed")
        outgoing = Message.objects.get(chat=self.message.chat, is_outgoing=True)
        self.assertEqual(outgoing.text, "Partial")
        self.assertEqual(outgoing.raw["stream"]["status"], "failed")
        response = self.client.post("/api/ai/retry/", {"chat_id": self.message.chat_id}, content_type="application/json")
        self.assertEqual(response.status_code, 202)
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, "QUEUED")
        self.api.responses.create.return_value = successful_events()
        self.assertTrue(self.process())
        self.assertEqual(ModelInvocation.objects.count(), 2)
        self.assertEqual(ModelInvocation.objects.filter(status="failed").count(), 1)

    def test_incomplete_response_retains_usage_and_is_not_finished(self):
        response = completed_response()
        response.update(status="incomplete", incomplete_details={"reason": "max_output_tokens"})
        self.api.responses.create.return_value = iter([
            event("response.output_text.delta", delta="Partial"),
            event("response.incomplete", response=response),
        ])
        self.assertFalse(self.process())
        attempt = ModelInvocation.objects.get()
        self.assertEqual(attempt.status, "incomplete")
        self.assertEqual(attempt.output_tokens, 8)
        self.assertEqual(Message.objects.get(chat=self.message.chat, is_outgoing=True).raw["stream"]["status"], "failed")

    def test_network_failure_records_an_attempt_without_tokens(self):
        self.api.responses.create.side_effect = RuntimeError("provider unavailable")
        self.assertFalse(self.process())
        attempt = ModelInvocation.objects.get()
        self.assertEqual(attempt.status, "failed")
        self.assertIsNone(attempt.output_tokens)
        self.assertEqual(Message.objects.get(chat=self.message.chat, is_outgoing=True).raw["stream"]["status"], "failed")

    def test_tools_persist_results_and_use_child_request_for_continuation(self):
        tool = Tool.objects.create(name="double", code="tool_definition = {'name': 'double', 'parameters': {'number': {'type': 'integer'}}, 'run': lambda number: {'value': number * 2}}")
        self.bot.tools.add(tool)
        response = completed_response(text="", output=[{
            "type": "function_call", "call_id": "call_double", "name": "double",
            "arguments": '{"number":21,"progress_updates_for_user":"Calculating the result"}',
        }])
        self.api.responses.create.return_value = iter([event("response.completed", response=response)])
        self.assertTrue(self.process())
        persisted = ToolCall.objects.get(call_id="call_double")
        self.assertEqual(persisted.status, "COMPLETED")
        self.assertEqual(persisted.result_status, "SUCCESS")
        child = Request.objects.get(parent_request=self.request)
        self.assertEqual(child.status, "QUEUED")
        self.api.responses.create.return_value = successful_events(completed_response(text="42"))
        with patch("core.integrations.bot.local_client", return_value=self.api):
            self.assertTrue(self.bot.process_request(child))
        self.assertEqual(ModelInvocation.objects.count(), 2)
        inputs = self.api.responses.create.call_args.kwargs["input"]
        self.assertTrue(any(item.get("type") == "function_call_output" for item in inputs))
        self.assertEqual(self.api.responses.create.call_args.kwargs["tools"][0]["parameters"]["required"], ["number", "progress_updates_for_user"])

    def test_tool_exception_becomes_persisted_error_result(self):
        tool = Tool.objects.create(name="broken", code="def run():\n    raise RuntimeError('broken')\ntool_definition = {'name': 'broken', 'parameters': {}, 'run': run}")
        self.bot.tools.add(tool)
        response = completed_response(text="", output=[{"type": "function_call", "call_id": "call_broken", "name": "broken", "arguments": '{}'}])
        self.api.responses.create.return_value = iter([event("response.completed", response=response)])
        self.assertTrue(self.process())
        self.assertEqual(ToolCall.objects.get(call_id="call_broken").result_status, "ERROR")
        self.assertEqual(Request.objects.get(parent_request=self.request).status, "QUEUED")

    def test_usage_and_retry_are_isolated_by_account(self):
        self.api.responses.create.return_value = successful_events()
        self.assertTrue(self.process())
        usage = self.client.get("/api/ai/usage/", {"chat_id": self.message.chat_id})
        self.assertEqual(usage.json()["totals"]["attempts"], 1)
        other = get_user_model().objects.create_user("other")
        self.client.force_login(other)
        self.assertEqual(self.client.get("/api/ai/usage/", {"chat_id": self.message.chat_id}).status_code, 404)
        self.assertEqual(self.client.post("/api/ai/retry/", {"chat_id": self.message.chat_id}, content_type="application/json").status_code, 404)

    def test_finished_turn_cannot_be_requeued(self):
        self.api.responses.create.return_value = successful_events()
        self.assertTrue(self.process())
        self.assertEqual(self.client.post("/api/ai/retry/", {"chat_id": self.message.chat_id}, content_type="application/json").status_code, 409)

    def test_continuation_with_prior_tool_calls_cannot_be_requeued(self):
        self.request.tool_call_count = 1
        self.request.save(update_fields=["tool_call_count"])
        Request.objects.create(
            message=self.message, account=self.request.account, channel=self.request.channel,
            parent_request=self.request, initial_request=self.request, status="FAILED",
        )
        self.assertEqual(self.client.post("/api/ai/retry/", {"chat_id": self.message.chat_id}, content_type="application/json").status_code, 409)

    def test_queue_cannot_append_to_another_accounts_chat(self):
        other = get_user_model().objects.create_user("other_chat")
        self.client.force_login(other)
        before = Message.objects.count()
        response = self.client.post("/api/ai/respond/", {"prompt": "Hello", "chat_id": self.message.chat_id}, content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Message.objects.count(), before)

    def test_failed_event_keeps_usage_and_closes_stream(self):
        response = completed_response()
        response["status"] = "failed"
        stream = Mock()
        stream.__iter__ = Mock(return_value=iter([event("response.failed", response=response)]))
        self.api.responses.create.return_value = stream
        self.assertFalse(self.process())
        stream.close.assert_called_once()
        attempt = ModelInvocation.objects.get()
        self.assertEqual(attempt.status, "failed")
        self.assertEqual(attempt.input_tokens, 12)

    def test_tool_limit_prevents_execution(self):
        response = completed_response(text="", output=[{"type": "function_call", "call_id": "over_limit", "name": "anything", "arguments": '{}'}])
        self.api.responses.create.return_value = iter([event("response.completed", response=response)])
        with self.settings(UNISTACK_MAX_TOOL_CALLS=0):
            self.assertFalse(self.process())
        self.assertFalse(ToolCall.objects.filter(call_id="over_limit").exists())
        self.assertEqual(Message.objects.get(chat=self.message.chat, is_outgoing=True).raw["stream"]["status"], "failed")


class ConfigurationTests(SimpleTestCase):
    @patch("core.management.commands.check_local_ai.local_client")
    def test_model_availability_check(self, factory):
        client = factory.return_value.__enter__.return_value
        client.models.list.return_value = [SimpleNamespace(id=settings.PORTACODE_LLM_MODEL)]
        call_command("check_local_ai")
        client.models.list.return_value = [SimpleNamespace(id="another-model")]
        with self.assertRaisesRegex(CommandError, "unavailable"):
            call_command("check_local_ai")

    def test_public_host_settings_are_read_at_runtime(self):
        path = Path(settings.BASE_DIR) / "config" / "settings.py"
        spec = importlib.util.spec_from_file_location("runtime_settings", path)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(os.environ, PORTACODE_PRIMARY_PUBLIC_URL="https://demo.example.test", PORTACODE_PRIMARY_PUBLIC_HOST="demo.example.test"):
            spec.loader.exec_module(module)
        self.assertIn("demo.example.test", module.ALLOWED_HOSTS)
        self.assertIn("https://demo.example.test", module.CSRF_TRUSTED_ORIGINS)
        self.assertEqual(module.DJANGO_PUBLIC_ORIGIN, "https://demo.example.test")
