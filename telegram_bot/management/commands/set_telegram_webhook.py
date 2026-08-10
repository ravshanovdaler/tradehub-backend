import json
import urllib.request
import urllib.error
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = "Sets the Telegram Bot webhook URL."

    def add_arguments(self, parser):
        parser.add_argument('url', type=str, help="The public HTTPS URL of your webhook endpoint (e.g., https://domain.com/api/telegram/webhook/)")

    def handle(self, *args, **options):
        token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        if not token:
            self.stderr.write(self.style.ERROR("TELEGRAM_BOT_TOKEN is not configured in settings."))
            return

        webhook_url = options['url']
        self.stdout.write(f"Setting webhook to: {webhook_url}")

        set_url = f"https://api.telegram.org/bot{token}/setWebhook?url={webhook_url}"
        req = urllib.request.Request(set_url)

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                res_data = json.loads(response.read().decode())
                if res_data.get("ok"):
                    self.stdout.write(self.style.SUCCESS(f"Success: {res_data.get('description')}"))
                else:
                    self.stderr.write(self.style.ERROR(f"Failed: {res_data}"))
        except urllib.error.URLError as e:
            self.stderr.write(self.style.ERROR(f"Network error: {e}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Unexpected error: {e}"))
