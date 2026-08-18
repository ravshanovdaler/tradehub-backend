import json
import logging
import threading
import urllib.request
import urllib.error
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import TelegramProfile
from .translations import TRANSLATIONS, get_text

logger = logging.getLogger(__name__)

User = get_user_model()

def send_telegram_message(chat_id, text, reply_markup=None):
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
    if reply_markup:
        payload["reply_markup"] = reply_markup

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

def answer_telegram_callback(callback_query_id, text=None):
    """Answers a Telegram callback query."""
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    if not token:
        return False

    url = f"https://api.telegram.org/bot{token}/answerCallbackQuery"
    payload = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={'Content-Type': 'application/json'}
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            res = json.loads(response.read().decode())
            return bool(res.get("ok"))
    except Exception as e:
        logger.error(f"Error answering Telegram callback query: {e}")
        return False

def _async_send_task(chat_id, text, reply_markup=None):
    try:
        send_telegram_message(chat_id, text, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error in async Telegram send: {e}")

def send_notification_to_user(user, text_or_key, **kwargs):
    """
    Asynchronously sends a Telegram notification to a user.
    If text_or_key is a key in TRANSLATIONS['en'], translates it to the user's preferred language.
    """
    try:
        profile = getattr(user, 'telegram_profile', None)
        if profile and profile.chat_id and profile.notifications_enabled:
            lang = profile.language or 'en'
            if text_or_key in TRANSLATIONS['en']:
                final_text = get_text(text_or_key, lang=lang, **kwargs)
            else:
                final_text = text_or_key

            thread = threading.Thread(target=_async_send_task, args=(profile.chat_id, final_text))
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
