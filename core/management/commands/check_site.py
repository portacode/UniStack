"""Render the foundation pages in both access modes before shipping changes."""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.test import Client, override_settings


class Command(BaseCommand):
    help = "Check public pages, auth links and chat/signup policy without creating accounts."

    def handle(self, *args, **options):
        for signup in (False, True):
            for guest in (False, True):
                with override_settings(
                    ALLOWED_HOSTS=[*settings.ALLOWED_HOSTS, "testserver"],
                    SECURE_SSL_REDIRECT=False,
                    UNISTACK_ALLOW_SIGNUP=signup,
                    UNISTACK_ALLOW_ANONYMOUS_CHAT=guest,
                ):
                    client = Client()
                    for path in ("/", "/accounts/login/", "/assistant/"):
                        try:
                            response = client.get(path)
                        except Exception as error:
                            raise CommandError(f"{path} failed with signup={signup}, guest_chat={guest}: {error}") from error
                        if response.status_code != 200:
                            raise CommandError(f"{path} returned {response.status_code}; preserve the shared public shell and auth routes")
                    response = client.get("/accounts/signup/")
                    if response.status_code != (200 if signup else 404):
                        raise CommandError("Keep the signup route and use UNISTACK_ALLOW_SIGNUP to control access")
        self.stdout.write(self.style.SUCCESS("Site pages render with signup and guest chat enabled or disabled"))
