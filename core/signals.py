"""Connect UniCom's guest history transfer to Django login (including signup)."""

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from unicom.models import Account
from unicom.services.webchat.migrate_guest_to_user import migrate_guest_to_user


@receiver(user_logged_in, dispatch_uid="unistack.transfer_guest_chat")
def transfer_guest_chat(sender, request, user, **kwargs):
    old_key = getattr(request, "unistack_guest_session_key", None)
    if old_key and Account.objects.filter(id=f"webchat_guest_{old_key}", platform="WebChat").exists():
        migrate_guest_to_user(old_key, user)
