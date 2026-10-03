import copy

from django.conf import settings
from django.db.models import F
from django.utils import timezone
from unibot.services.llm_handler import build_openai_tools
from unibot.services.tool_exceptions import ToolHandlerError, ToolHandlerWarning
from unibot.services.tool_result_handler import handle_tool_result, prepare_file_response
from unicom.services.webchat.streaming import WebChatMessageStreamSink

from core.integrations.client import ObservedClient, ResponseFailure, local_client
from core.integrations.upstream_responses import create_response
from core.models import ModelInvocation


def strict_schema(schema):
    schema = copy.deepcopy(schema)
    schema.pop("default", None)
    for property_name, property_schema in schema.get("properties", {}).items():
        schema["properties"][property_name] = strict_schema(property_schema)
    if schema.get("type") == "object":
        schema["additionalProperties"] = False
        schema["required"] = list(schema.get("properties", {}))
    if isinstance(schema.get("items"), dict):
        schema["items"] = strict_schema(schema["items"])
    for union in ("anyOf", "oneOf", "allOf"):
        if union in schema:
            schema[union] = [strict_schema(item) for item in schema[union]]
    return schema


def execute_tools(result, bot, message, tools_list, request, client, auto_params):
    if request is None:
        raise ValueError("Responses tools require a persisted UniCom request")
    root = request.initial_request or request
    if root.tool_call_count + sum(type(request).objects.filter(initial_request=root).values_list("tool_call_count", flat=True)) + len(result.tool_calls) > settings.UNISTACK_MAX_TOOL_CALLS:
        raise ValueError("This conversation turn reached its tool-call limit")
    calls = request.submit_tool_calls([
        {"name": call.name, "arguments": dict(call.arguments), "id": call.call_id, "auto_params": auto_params.get(call.name, [])}
        for call in result.tool_calls
    ])
    for call, persisted in zip(result.tool_calls, calls):
        _, tool_map, injected = build_openai_tools(
            tools_list, bot=bot, message=message, openai_client=client,
            request=request, tool_call=persisted,
        )
        arguments = dict(call.arguments)
        for name in injected.get(call.name, []):
            arguments.pop(name, None)
        status = "SUCCESS"
        try:
            value = tool_map[call.name](**arguments)
        except (ToolHandlerError, ToolHandlerWarning) as error:
            status = error.status
            value = error.payload if error.payload is not None else {"error": str(error)}
        except Exception:
            status, value = "ERROR", {"error": "The tool failed to execute"}
        if value is None:
            persisted.mark_active()
            continue
        file_path = handle_tool_result(value)
        if file_path:
            message.reply_with(prepare_file_response([file_path], message.platform))
            value = "File provided to the user"
        persisted.respond(value, status=status)


def reply(message, bot, tools_list, request=None, client=None):
    if client is not None:
        return _reply(message, bot, tools_list, request, client)
    owned_client = local_client()
    try:
        return _reply(message, bot, tools_list, request, owned_client)
    finally:
        owned_client.close()


def _reply(message, bot, tools_list, request, client):
    invocation = ModelInvocation.objects.create(
        chat_id=message.chat_id, request_id=getattr(request, "pk", None),
        model=settings.PORTACODE_LLM_MODEL,
    )
    projection = WebChatMessageStreamSink(message) if message.platform == "WebChat" else None

    def events(event):
        if projection is None:
            return
        event_types = {"response.started": "started", "response.text.delta": "text.delta", "response.finished": "finished", "response.failed": "failed"}
        event = {**event, "type": event_types[event["type"]]}
        if event["type"] == "failed":
            event["error"] = "The AI response did not complete. You can retry this message."
        projection(event)
        if projection.message and event["type"] != "text.delta":
            raw = dict(projection.message.raw or {})
            raw["ai"] = {"invocation_id": str(invocation.pk), "request_id": str(request.pk) if request else None, "model": invocation.model}
            projection.message.raw = raw
            projection.message.save(update_fields=["raw"])

    try:
        messages = message.as_llm_chat(
            depth=129, mode="chat", multimodal=True,
            system_instruction="You are UniStack AI. Answer clearly, directly, and helpfully.",
        )
        tools, _, auto_params = build_openai_tools(tools_list, bot=bot, message=message, openai_client=client, request=request)
        for tool in tools:
            tool["function"]["parameters"] = strict_schema(tool["function"]["parameters"])
        result = create_response(
            client=ObservedClient(client, invocation), model=invocation.model,
            messages=messages, tools=tools, stream=projection is not None,
            event_sink=events, stream_id=str(invocation.pk), store=False,
            reasoning={"effort": settings.PORTACODE_REASONING_EFFORT},
        )
        invocation.status = "completed"
    except Exception as error:
        invocation.status = error.status if isinstance(error, ResponseFailure) else "failed"
        invocation.error = "The AI request did not complete" if not isinstance(error, ResponseFailure) else str(error)
        if projection and projection.message is None:
            events({"type": "response.failed"})
        raise
    finally:
        usage = invocation.usage or {}
        invocation.input_tokens = usage.get("input_tokens")
        invocation.output_tokens = usage.get("output_tokens")
        invocation.cached_input_tokens = (usage.get("input_tokens_details") or {}).get("cached_tokens")
        invocation.reasoning_tokens = (usage.get("output_tokens_details") or {}).get("reasoning_tokens")
        invocation.finished_at = timezone.now()
        invocation.save()
        if request is not None:
            type(request).objects.filter(pk=request.pk).update(
                llm_calls_count=F("llm_calls_count") + 1,
                llm_token_usage=F("llm_token_usage") + (usage.get("total_tokens") or 0),
            )
    outgoing = projection.message if projection else None
    if projection is None and result.text:
        outgoing = message.reply_with({"type": "text", "text": result.text})
    if result.tool_calls:
        if projection and not result.text:
            events({"type": "response.finished", "text": "Using tools…", "response_id": result.response_id})
        try:
            execute_tools(result, bot, message, tools_list, request, client, auto_params)
        except Exception:
            events({"type": "response.failed", "response_id": result.response_id})
            raise
    return outgoing
