from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from unibot.models import Bot
from unicom.models import Account, Channel, Message
from core.branding import get_brand


class Command(BaseCommand):
    help = "Synchronize UniStack's source-defined streaming bot and WebChat channel."

    def handle(self, *args, **options):
        call_command("sync_tools_and_bots", verbosity=options["verbosity"])
        try:
            bot = Bot.objects.select_related("request_category").get(name="unistack")
        except Bot.DoesNotExist as error:
            raise CommandError("The source-defined unistack bot was not synced") from error
        category = bot.request_category
        if category is None:
            raise CommandError("The UniStack bot has no request category")
        category.is_public = True
        category.is_active = True
        category.save(update_fields=["is_public", "is_active"])
        channel, _ = Channel.objects.get_or_create(
            name="UniStack WebChat", platform="WebChat", defaults={"config": {}}
        )
        channel.validate()
        channel.refresh_from_db()
        if not channel.active:
            raise CommandError("The UniStack WebChat channel could not be activated")
        category.allowed_channels.set([channel])
        # Keep the stable internal channel identity while branding the sender
        # rendered by UniCom. Its helper otherwise defaults to channel.name.
        display_name = f"{get_brand()['name']} assistant"[:100]
        sender, _ = Account.objects.update_or_create(
            id=f"webchat_bot_{channel.pk}",
            defaults={"channel": channel, "platform": "WebChat", "is_bot": True,
                      "name": display_name, "raw": {"channel_id": channel.pk}},
        )
        Message.objects.filter(channel=channel, sender=sender, is_outgoing=True).update(
            sender_name=display_name,
        )
        self.stdout.write(self.style.SUCCESS("UniStack streaming WebChat is ready"))
