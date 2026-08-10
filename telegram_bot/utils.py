import json
import logging
import threading
import urllib.request
import urllib.error
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import TelegramProfile

logger = logging.getLogger(__name__)

User = get_user_model()

def send_telegram_message(chat_id, text):
    """Sends a message to the specified Telegram chat ID using urllib.request."""
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN is not configured in settings.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={'Content-Type': 'application/json'}
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            res = json.loads(response.read().decode())
            if res.get("ok"):
                return True
            else:
                logger.error(f"Telegram API returned error: {res}")
                return False
    except urllib.error.URLError as e:
        logger.error(f"Failed to connect to Telegram API: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending Telegram message: {e}")
        return False

def _async_send_task(chat_id, text):
    try:
        send_telegram_message(chat_id, text)
    except Exception as e:
        logger.error(f"Error in async Telegram send: {e}")

def send_notification_to_user(user, text):
    """Asynchronously sends a Telegram notification to a user if they have linked their account."""
    try:
        profile = getattr(user, 'telegram_profile', None)
        if profile and profile.chat_id and profile.notifications_enabled:
            # Run in a background thread to prevent blocking database save operations
            thread = threading.Thread(target=_async_send_task, args=(profile.chat_id, text))
            thread.daemon = True
            thread.start()
            return True
    except Exception as e:
        logger.error(f"Error checking Telegram profile for notifications: {e}")
    return False

def link_telegram_account(user, chat_id):
    """Links a Telegram chat ID to a Django user."""
    # First, if another user is linked to this chat_id, unlink them (chat_id must be unique)
    TelegramProfile.objects.filter(chat_id=chat_id).exclude(user=user).update(chat_id=None)

    # Now get or create the profile for the current user and link it
    profile, _ = TelegramProfile.objects.get_or_create(user=user)
    profile.chat_id = chat_id
    profile.auth_token = None  # Clear the token once successfully linked
    profile.save()
    return profile
