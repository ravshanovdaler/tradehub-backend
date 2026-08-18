import time
import json
import logging
import urllib.request
import urllib.error
from django.core.management.base import BaseCommand
from django.conf import settings
from telegram_bot.bot_logic import handle_telegram_message, handle_telegram_callback_query

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Runs a long-polling loop to get updates from the Telegram Bot API (for local testing)."

    def handle(self, *args, **options):
        token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        if not token:
            self.stderr.write(self.style.ERROR("TELEGRAM_BOT_TOKEN is not configured in settings."))
            return

        self.stdout.write(self.style.SUCCESS("Starting Telegram Long Polling Bot..."))
        self.stdout.write(f"Bot Username: @{getattr(settings, 'TELEGRAM_BOT_USERNAME', 'unknown')}")
        self.stdout.write("Press Ctrl+C to exit.")

        offset = 0
        url = f"https://api.telegram.org/bot{token}/getUpdates"

        while True:
            try:
                poll_url = f"{url}?offset={offset}&timeout=30"
                req = urllib.request.Request(poll_url)
                with urllib.request.urlopen(req, timeout=35) as response:
                    res_data = json.loads(response.read().decode())
                    if not res_data.get("ok"):
                        self.stderr.write(f"Telegram API Error: {res_data}")
                        time.sleep(5)
                        continue

                    updates = res_data.get("result", [])
                    for update in updates:
                        update_id = update["update_id"]
                        offset = update_id + 1

                        if "message" in update:
                            message = update["message"]
                            chat_id = message.get("chat", {}).get("id")
                            text = message.get("text")
                            sender_username = message.get("from", {}).get("username", "unknown")

                            if chat_id and text:
                                self.stdout.write(self.style.HTTP_INFO(f"Received message from @{sender_username} ({chat_id}): {text}"))
                                try:
                                    handle_telegram_message(chat_id, text)
                                except Exception as e:
                                    self.stderr.write(self.style.ERROR(f"Error handling message: {e}"))

                        elif "callback_query" in update:
                            cb_query = update["callback_query"]
                            data = cb_query.get("data")
                            sender_username = cb_query.get("from", {}).get("username", "unknown")
                            self.stdout.write(self.style.HTTP_INFO(f"Received callback from @{sender_username}: {data}"))
                            try:
                                handle_telegram_callback_query(cb_query)
                            except Exception as e:
                                self.stderr.write(self.style.ERROR(f"Error handling callback query: {e}"))

            except KeyboardInterrupt:
                self.stdout.write(self.style.SUCCESS("\nExiting polling loop..."))
                break
            except urllib.error.URLError as e:
                self.stderr.write(self.style.WARNING(f"Network error in getUpdates: {e}"))
                time.sleep(5)
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Unexpected error: {e}"))
                time.sleep(5)
