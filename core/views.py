import json
from django.conf import settings
from django.db import connection
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from openai import OpenAI, OpenAIError

@ensure_csrf_cookie
def home(request):
    from unicom.models import Channel
    channel = Channel.objects.filter(name="UniStack WebChat", platform="WebChat").first()
    return render(request, "core/home.html", {"model": settings.PORTACODE_LLM_MODEL, "channel": channel})

def health(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return JsonResponse({"status": "ok", "stack": ["django", "unicom", "unicrm", "unibot"]})

@login_required(login_url="/admin/login/")
@require_POST
def ai_respond(request):
    try:
        payload = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Body must be valid JSON."}, status=400)
    if not isinstance(payload, dict):
        return JsonResponse({"error": "Body must be a JSON object."}, status=400)
    prompt = str(payload.get("prompt", "")).strip()
    if not prompt:
        return JsonResponse({"error": "prompt is required."}, status=400)
    if len(prompt) > 8000:
        return JsonResponse({"error": "Please keep prompts under 8,000 characters."}, status=400)
    client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL, timeout=60, max_retries=1)
    try:
        response = client.responses.create(
            model=settings.PORTACODE_LLM_MODEL,
            instructions="You are the helpful assistant inside a general-purpose UniStack Django application.",
            input=prompt,
            store=False,
        )
    except OpenAIError:
        return JsonResponse({"error": "The local AI service is unavailable. Check the device connection and try again."}, status=502)
    return JsonResponse({"response": response.output_text, "model": settings.PORTACODE_LLM_MODEL})
