from django.http import JsonResponse
from django.conf import settings
from django.middleware.csrf import CsrfViewMiddleware


class WebChatAccessMiddleware(CsrfViewMiddleware):
    def process_request(self, request):
        # Django rotates the session key during login. Retain the guest key
        # for UniCom's migration helper before AuthenticationMiddleware's view.
        request.unistack_guest_session_key = request.session.session_key
        return super().process_request(request)

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if not request.path.startswith("/unicom/webchat/"):
            return None
        if not request.user.is_authenticated and not settings.UNISTACK_ALLOW_ANONYMOUS_CHAT:
            return JsonResponse({"error": "Sign in to use UniStack chat."}, status=401)
        return super().process_view(request, lambda: None, callback_args, callback_kwargs)
