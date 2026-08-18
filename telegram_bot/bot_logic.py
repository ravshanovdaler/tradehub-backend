import logging
from django.contrib.auth import authenticate, get_user_model
from .models import TelegramProfile
from .utils import link_telegram_account, send_telegram_message, answer_telegram_callback
from .translations import get_text, LANGUAGE_NAMES

logger = logging.getLogger(__name__)
User = get_user_model()

def get_profile_language(chat_id):
    """Retrieves language preference for a given chat_id, default 'en'."""
    try:
        profile = TelegramProfile.objects.filter(chat_id=str(chat_id)).first()
        if profile and profile.language:
            return profile.language
    except Exception as e:
        logger.error(f"Error fetching profile language: {e}")
    return 'en'

def set_profile_language(chat_id, lang_code):
    """Sets language preference for a profile with the given chat_id."""
    if lang_code not in ['en', 'ru', 'uz']:
        return False
    try:
        profile = TelegramProfile.objects.filter(chat_id=str(chat_id)).first()
        if profile:
            profile.language = lang_code
            profile.save()
            return True
    except Exception as e:
        logger.error(f"Error setting profile language: {e}")
    return False

def get_language_keyboard():
    """Returns Telegram InlineKeyboardMarkup for language selection."""
    return {
        "inline_keyboard": [
            [
                {"text": "🇬🇧 English", "callback_data": "set_lang_en"},
                {"text": "🇷🇺 Русский", "callback_data": "set_lang_ru"},
                {"text": "🇺🇿 Oʻzbekcha", "callback_data": "set_lang_uz"}
            ]
        ]
    }

def handle_telegram_message(chat_id, text):
    """Processes a message received from Telegram and sends localized response."""
    if not text:
        return

    chat_id = str(chat_id)
    text = text.strip()
    parts = text.split()
    command = parts[0].lower() if parts else ""
    lang = get_profile_language(chat_id)

    if command == "/start":
        if len(parts) > 1:
            token = parts[1]
            try:
                profile = TelegramProfile.objects.get(auth_token=token)
                link_telegram_account(profile.user, chat_id)
                user_lang = profile.language or 'en'
                msg = get_text('welcome_linked', lang=user_lang, username=profile.user.username)
                send_telegram_message(chat_id, msg)
            except TelegramProfile.DoesNotExist:
                msg = get_text('invalid_token', lang=lang)
                send_telegram_message(chat_id, msg)
        else:
            msg = get_text('welcome_unlinked', lang=lang)
            send_telegram_message(chat_id, msg, reply_markup=get_language_keyboard())

    elif command in ["/language", "/lang"]:
        if len(parts) > 1:
            code = parts[1].lower()
            if code in ['en', 'ru', 'uz']:
                set_profile_language(chat_id, code)
                confirm_msg = get_text('language_changed', lang=code)
                send_telegram_message(chat_id, confirm_msg)
            else:
                msg = get_text('language_prompt', lang=lang)
                send_telegram_message(chat_id, msg, reply_markup=get_language_keyboard())
        else:
            msg = get_text('language_prompt', lang=lang)
            send_telegram_message(chat_id, msg, reply_markup=get_language_keyboard())

    elif command == "/login":
        if len(parts) < 3:
            msg = get_text('login_usage', lang=lang)
            send_telegram_message(chat_id, msg)
            return

        identifier = parts[1]
        password = parts[2]

        user_obj = User.objects.filter(username=identifier).first()
        if not user_obj:
            user_obj = User.objects.filter(email=identifier).first()
        if not user_obj:
            user_obj = User.objects.filter(phone_number=identifier).first()

        if not user_obj:
            msg = get_text('user_not_found', lang=lang)
            send_telegram_message(chat_id, msg)
            return

        user = authenticate(username=user_obj.username, password=password)
        if user:
            if user.deletion_requested:
                msg = get_text('account_pending_deletion', lang=lang)
                send_telegram_message(chat_id, msg)
                return

            profile = link_telegram_account(user, chat_id)
            user_lang = profile.language or lang
            msg = get_text('login_success', lang=user_lang, username=user.username)
            send_telegram_message(chat_id, msg)
        else:
            msg = get_text('login_invalid_password', lang=lang)
            send_telegram_message(chat_id, msg)

    elif command == "/logout":
        try:
            profile = TelegramProfile.objects.get(chat_id=chat_id)
            username = profile.user.username
            user_lang = profile.language or lang
            profile.chat_id = None
            profile.save()
            msg = get_text('logout_success', lang=user_lang, username=username)
            send_telegram_message(chat_id, msg)
        except TelegramProfile.DoesNotExist:
            msg = get_text('logout_not_logged_in', lang=lang)
            send_telegram_message(chat_id, msg)

    elif command == "/status":
        try:
            profile = TelegramProfile.objects.get(chat_id=chat_id)
            user = profile.user
            user_lang = profile.language or lang
            role = "Seller" if user.is_seller else "Buyer" if user.is_buyer else "Staff/Admin"
            notifications = get_text('enabled' if profile.notifications_enabled else 'disabled', lang=user_lang)
            language_name = LANGUAGE_NAMES.get(user_lang, 'English 🇬🇧')
            msg = get_text(
                'status_linked',
                lang=user_lang,
                username=user.username,
                role=role,
                language_name=language_name,
                notifications=notifications
            )
            send_telegram_message(chat_id, msg)
        except TelegramProfile.DoesNotExist:
            language_name = LANGUAGE_NAMES.get(lang, 'English 🇬🇧')
            msg = get_text('status_unlinked', lang=lang, language_name=language_name)
            send_telegram_message(chat_id, msg)

    elif command == "/help":
        msg = get_text('help_text', lang=lang)
        send_telegram_message(chat_id, msg)

    else:
        msg = get_text('unknown_command', lang=lang)
        send_telegram_message(chat_id, msg)

def handle_telegram_callback_query(callback_query):
    """Processes callback query payloads from inline button clicks."""
    callback_query_id = callback_query.get("id")
    data = callback_query.get("data", "")
    message = callback_query.get("message", {})
    chat_id = str(message.get("chat", {}).get("id", ""))

    if not chat_id or not data:
        return

    if data.startswith("set_lang_"):
        lang_code = data.replace("set_lang_", "")
        if lang_code in ['en', 'ru', 'uz']:
            set_profile_language(chat_id, lang_code)
            if callback_query_id:
                answer_telegram_callback(callback_query_id)
            confirm_msg = get_text('language_changed', lang=lang_code)
            send_telegram_message(chat_id, confirm_msg)
