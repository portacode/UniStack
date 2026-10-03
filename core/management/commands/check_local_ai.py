from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from openai import OpenAIError

from core.integrations.client import local_client


class Command(BaseCommand):
    help = "Verify the configured model exists on the local Portacode Responses API."

    def handle(self, *args, **options):
        try:
            with local_client() as client:
                models = {model.id for model in client.models.list()}
        except OpenAIError as error:
            raise CommandError("The local Portacode API is unavailable; check the device and Codex connection") from error
        if settings.PORTACODE_LLM_MODEL not in models:
            raise CommandError(f"Configured model {settings.PORTACODE_LLM_MODEL!r} is unavailable; update PORTACODE_LLM_MODEL to one of: {', '.join(sorted(models))}")
        self.stdout.write(self.style.SUCCESS(f"Local AI model {settings.PORTACODE_LLM_MODEL} is available"))
