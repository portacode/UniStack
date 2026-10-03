from types import SimpleNamespace

from django.conf import settings
from openai import OpenAI

from core.integrations.upstream_responses import _as_dict


class ResponseFailure(RuntimeError):
    def __init__(self, status, message):
        self.status = status
        super().__init__(message)


def local_client():
    return OpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
        timeout=settings.PORTACODE_RESPONSE_TIMEOUT,
        max_retries=0,
    )


class ObservedClient:
    def __init__(self, client, invocation):
        self.client = client
        self.invocation = invocation
        self.responses = SimpleNamespace(create=self.create)

    def capture(self, response):
        data = _as_dict(response)
        self.invocation.response_id = data.get("id") or self.invocation.response_id
        self.invocation.usage = data.get("usage") or self.invocation.usage
        status = data.get("status")
        if status and status != "completed":
            detail = data.get("incomplete_details") or data.get("error") or {}
            reason = detail.get("reason") or detail.get("code") or status
            raise ResponseFailure("incomplete" if status == "incomplete" else "failed", f"AI response {status}: {reason}")

    def create(self, **kwargs):
        if kwargs.get("stream"):
            return self.events(**kwargs)
        response = self.client.responses.create(**kwargs)
        self.capture(response)
        return response

    def events(self, **kwargs):
        stream = self.client.responses.create(**kwargs)
        try:
            for event in stream:
                data = _as_dict(event)
                event_type = data.get("type")
                if event_type == "response.created":
                    self.invocation.response_id = (data.get("response") or {}).get("id") or self.invocation.response_id
                if event_type in {"response.completed", "response.failed", "response.incomplete"}:
                    response = data.get("response") or {}
                    self.capture(response)
                    if event_type != "response.completed":
                        status = "incomplete" if event_type == "response.incomplete" else "failed"
                        raise ResponseFailure(status, f"AI response {status}")
                if event_type == "error":
                    raise ResponseFailure("failed", "The AI provider reported a streaming error")
                yield event
        finally:
            close = getattr(stream, "close", None)
            if callable(close):
                close()
