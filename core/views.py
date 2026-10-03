import json
from django.conf import settings
from django.db import connection
from django.db import transaction
from django.db.models import Sum, Count, Q
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse, Http404
from django.views.static import serve
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from unicom.models import Channel, Request, Message
from unicom.services.webchat.save_webchat_message import save_webchat_message
from unicom.models import AccountChat
from core.models import ModelInvocation

chat_access_required = user_passes_test(
    lambda user: user.is_authenticated or settings.UNISTACK_ALLOW_ANONYMOUS_CHAT,
    login_url="/admin/login/",
)


def webchat_account_id(request):
    if request.user.is_authenticated:
        return f"webchat_user_{request.user.pk}"
    return f"webchat_guest_{request.session.session_key}" if request.session.session_key else None


@chat_access_required
def protected_media(request, path):
    # Guest attachments need the same conversation ownership checks as text.
    webchat_files = Message.objects.filter(media=path, platform="WebChat")
    # Keep administrative inspection and existing non-chat CRM media working.
    if request.user.is_authenticated and (
        request.user.is_staff or not webchat_files.exists()
    ):
        return serve(request, path, document_root=settings.MEDIA_ROOT)
    account_id = webchat_account_id(request)
    if not account_id or not webchat_files.filter(
        chat__accountchat__account_id=account_id,
    ).exists():
        raise Http404("Attachment not found")
    return serve(request, path, document_root=settings.MEDIA_ROOT)


@ensure_csrf_cookie
def home(request):
    channel = Channel.objects.filter(name="UniStack WebChat", platform="WebChat").first()
    return render(request, "core/home.html", {
        "model": settings.PORTACODE_LLM_MODEL, "channel": channel,
        "chat_enabled": request.user.is_authenticated or settings.UNISTACK_ALLOW_ANONYMOUS_CHAT,
    })

def health(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return JsonResponse({"status": "ok", "stack": ["django", "unicom", "unicrm", "unibot"]})

@chat_access_required
@require_POST
def ai_respond(request):
    try:
        payload = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Body must be valid JSON."}, status=400)
    if not isinstance(payload, dict):
        return JsonResponse({"error": "Body must be a JSON object."}, status=400)
    if not isinstance(payload.get("prompt"), str):
        return JsonResponse({"error": "prompt must be a string."}, status=400)
    if payload.get("chat_id") is not None and not isinstance(payload["chat_id"], str):
        return JsonResponse({"error": "chat_id must be a string."}, status=400)
    prompt = payload["prompt"].strip()
    if not prompt:
        return JsonResponse({"error": "prompt is required."}, status=400)
    if len(prompt) > 8000:
        return JsonResponse({"error": "Please keep prompts under 8,000 characters."}, status=400)
    channel = Channel.objects.filter(name="UniStack WebChat", platform="WebChat", active=True).first()
    if channel is None:
        return JsonResponse({"error": "The demo bot/channel has not been synchronized."}, status=503)
    try:
        message = save_webchat_message(
            channel, {"text": prompt, "chat_id": payload.get("chat_id")}, request,
            user=request.user if request.user.is_authenticated else None,
        )
    except ValueError:
        return JsonResponse({"error": "The requested chat is unavailable."}, status=400)
    if message is None:
        return JsonResponse({"error": "This account cannot send messages."}, status=403)
    queued = Request.objects.filter(message=message).first()
    return JsonResponse({
        "status": "queued", "chat_id": message.chat_id, "message_id": message.pk,
        "request_id": str(queued.pk) if queued else None,
        "messages_url": f"/unicom/webchat/messages/?channel_id={channel.pk}&chat_id={message.chat_id}",
    }, status=202)


@chat_access_required
@require_POST
def retry_failed(request):
    try:
        payload = json.loads(request.body or b"{}")
        chat_id = payload.get("chat_id") if isinstance(payload, dict) else None
    except json.JSONDecodeError:
        chat_id = None
    if not isinstance(chat_id, str):
        return JsonResponse({"error": "chat_id is required."}, status=400)
    account_id = webchat_account_id(request)
    if not account_id:
        return JsonResponse({"error": "Chat not found."}, status=404)
    with transaction.atomic():
        failed = Request.objects.select_for_update().filter(
            account_id=account_id, message__chat_id=chat_id,
        ).order_by("-created_at").first()
        if failed is None:
            return JsonResponse({"error": "Chat not found."}, status=404)
        root_id = failed.initial_request_id or failed.pk
        made_tool_calls = Request.objects.filter(
            Q(pk=root_id) | Q(initial_request_id=root_id), tool_call_count__gt=0,
        ).exists()
        if failed.status != "FAILED" or made_tool_calls:
            return JsonResponse({"error": "This turn cannot be retried safely. Send a new message to continue."}, status=409)
        failed.status = "QUEUED"
        failed.error = None
        failed.save(update_fields=["status", "error"])
    return JsonResponse({"status": "queued", "request_id": str(failed.pk)}, status=202)


@chat_access_required
def usage(request):
    chat_id = request.GET.get("chat_id")
    if not AccountChat.objects.filter(chat_id=chat_id, account_id=webchat_account_id(request)).exists():
        return JsonResponse({"error": "Chat not found."}, status=404)
    invocations = ModelInvocation.objects.filter(chat_id=chat_id)
    totals = invocations.aggregate(
        attempts=Count("pk"), input_tokens=Sum("input_tokens"), output_tokens=Sum("output_tokens"),
        cached_input_tokens=Sum("cached_input_tokens"), reasoning_tokens=Sum("reasoning_tokens"),
    )
    return JsonResponse({
        "chat_id": chat_id, "totals": totals,
        "attempts": list(invocations.values("id", "request_id", "model", "status", "response_id", "input_tokens", "output_tokens", "started_at", "finished_at")),
        "note": "Token usage reported by the local API. Monetary charges are recorded by Portacode.",
    })
