"""Render the foundation pages in both access modes before shipping changes."""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.test import Client, override_settings
from django.contrib.auth import get_user_model
from core.shell_checks import check_shell, project_page_paths


class Command(BaseCommand):
    help = "Check public pages, auth links and chat/signup policy without creating accounts."

    def add_arguments(self, parser):
        parser.add_argument("--username", help="Also check private navigation using this existing test account")

    def check_page(self, client, path):
        if not path.startswith("/") or path.startswith("//"):
            raise CommandError(f"Navigation destination must be a local app route: {path}")
        try:
            response = client.get(path)
            if response.status_code != 200:
                raise ValueError(f"returned {response.status_code}")
            check_shell(response)
        except Exception as error:
            raise CommandError(f"{path}: {error}") from error

    def check_project_pages(self, client):
        for path in sorted(project_page_paths()):
            response = client.get(path)
            # POST-only actions, JSON APIs and login redirects are not pages.
            if response.status_code in (301, 302, 303, 307, 308, 403, 405):
                continue
            if response.status_code >= 500:
                raise CommandError(f"Project route {path} returned {response.status_code}")
            if response.status_code == 200 and 'text/html' in response.get('Content-Type', '') and b'<html' in response.content.lower():
                try:
                    check_shell(response)
                except ValueError as error:
                    raise CommandError(f"Project route {path}: {error}") from error

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
                    paths = {"/", "/accounts/login/", "/assistant/"}
                    paths.update(item["url"] for item in settings.SITE_NAVIGATION if not item.get("authenticated"))
                    for path in sorted(paths):
                        self.check_page(client, path)
                    response = client.get("/accounts/signup/")
                    if response.status_code != (200 if signup else 404):
                        raise CommandError("Keep the signup route and use UNISTACK_ALLOW_SIGNUP to control access")
                    if signup:
                        check_shell(response)
                    self.check_project_pages(client)
        if options.get("username"):
            model = get_user_model()
            try:
                user = model.objects.get(**{model.USERNAME_FIELD: options["username"]})
            except model.DoesNotExist as error:
                raise CommandError("Use an existing test account for --username") from error
            with override_settings(ALLOWED_HOSTS=[*settings.ALLOWED_HOSTS, "testserver"], SECURE_SSL_REDIRECT=False):
                client = Client()
                client.force_login(user)
                try:
                    for path in sorted({"/", "/assistant/", *(item["url"] for item in settings.SITE_NAVIGATION)}):
                        self.check_page(client, path)
                    self.check_project_pages(client)
                finally:
                    client.logout()
        elif any(item.get("authenticated") for item in settings.SITE_NAVIGATION):
            self.stdout.write("Private navigation not checked: run check_site --username <test-account> to validate it.")
        self.stdout.write(self.style.SUCCESS("Site pages render with signup and guest chat enabled or disabled"))
