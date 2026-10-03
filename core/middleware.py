from django.http import JsonResponse
from django.middleware.csrf import CsrfViewMiddleware


class WebChatAccessMiddleware(CsrfViewMiddleware):
    def process_view(self, request, callback, callback_args, callback_kwargs):
        if not request.path.startswith("/unicom/webchat/"):
            return None
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Sign in to use UniStack chat."}, status=401)
        return super().process_view(request, lambda: None, callback_args, callback_kwargs)
