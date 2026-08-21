import json
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from openai import OpenAI

def home(request):
    return render(request, "core/home.html", {"model": settings.PORTACODE_LLM_MODEL})

def health(request):
    return JsonResponse({"status": "ok", "stack": ["django", "unicom", "unicrm", "unibot"]})

@csrf_exempt
@require_POST
def ai_respond(request):
    try:
        payload = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Body must be valid JSON."}, status=400)
    prompt = str(payload.get("prompt", "")).strip()
    if not prompt:
        return JsonResponse({"error": "prompt is required."}, status=400)
    client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL)
    response = client.responses.create(
        model=settings.PORTACODE_LLM_MODEL,
        instructions="You are the helpful assistant inside a general-purpose UniStack Django application.",
        input=prompt,
        store=False,
    )
    return JsonResponse({"response": response.output_text, "model": settings.PORTACODE_LLM_MODEL})
