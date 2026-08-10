import logging
from django.contrib.auth import authenticate, get_user_model
from .models import TelegramProfile
from .utils import link_telegram_account, send_telegram_message

logger = logging.getLogger(__name__)
User = get_user_model()

def handle_telegram_message(chat_id, text):
    """Processes a message received from Telegram and returns/sends the response."""
    if not text:
        return

    text = text.strip()
    parts = text.split()
    command = parts[0].lower() if parts else ""

    if command == "/start":
        if len(parts) > 1:
            token = parts[1]
            try:
                profile = TelegramProfile.objects.get(auth_token=token)
                link_telegram_account(profile.user, chat_id)
                send_telegram_message(
                    chat_id,
                    f"🎉 *Success!* Your account *{profile.user.username}* has been successfully linked to TradeHub.\n\n"
                    "You will now receive notifications here for sales, new messages, and status updates."
                )
            except TelegramProfile.DoesNotExist:
                send_telegram_message(
                    chat_id,
                    "❌ *Invalid Link Code.*\n"
                    "Please generate a new linking code from your profile settings on the website."
                )
        else:
            send_telegram_message(
                chat_id,
                "👋 *Welcome to TradeHub Bot!*\n\n"
                "I can notify you when you get new orders (sales), chat messages, and KYC status updates.\n\n"
                "To link your account, you can:\n"
                "1. Log in on the website, go to your profile, and click *Link Telegram Bot*.\n"
                "2. Or, log in directly here using the command:\n"
                "   `/login <username_or_email> <password>`"
            )

    elif command == "/login":
        if len(parts) < 3:
            send_telegram_message(
                chat_id,
                "⚠️ *Usage:*\n"
                "`/login <username_or_email_or_phone> <password>`\n\n"
                "Example:\n"
                "`/login daler mysecurepassword`"
            )
            return

        identifier = parts[1]
        password = parts[2]

        # Authenticate user (supporting username, email, or phone)
        user_obj = None
        user_obj = User.objects.filter(username=identifier).first()
        if not user_obj:
            user_obj = User.objects.filter(email=identifier).first()
        if not user_obj:
            user_obj = User.objects.filter(phone_number=identifier).first()

        if not user_obj:
            send_telegram_message(chat_id, "❌ *Error:* No user found with that identifier.")
            return

        user = authenticate(username=user_obj.username, password=password)
        if user:
            if user.deletion_requested:
                send_telegram_message(chat_id, "❌ *Error:* This account is pending deletion.")
                return

            link_telegram_account(user, chat_id)
            send_telegram_message(
                chat_id,
                f"🎉 *Success!* Logged in successfully as *{user.username}*.\n\n"
                "Your Telegram is now linked to TradeHub."
            )
        else:
            send_telegram_message(chat_id, "❌ *Error:* Invalid password.")

    elif command == "/logout":
        try:
            profile = TelegramProfile.objects.get(chat_id=chat_id)
            username = profile.user.username
            profile.chat_id = None
            profile.save()
            send_telegram_message(chat_id, f"🔌 *Logged out.* Account *{username}* has been unlinked from this Telegram.")
        except TelegramProfile.DoesNotExist:
            send_telegram_message(chat_id, "ℹ️ You are not logged in or linked to any TradeHub account.")

    elif command == "/status":
        try:
            profile = TelegramProfile.objects.get(chat_id=chat_id)
            user = profile.user
            role = "Seller" if user.is_seller else "Buyer" if user.is_buyer else "Staff/Admin"
            send_telegram_message(
                chat_id,
                f"ℹ️ *Status: Linked*\n"
                f"• *Username:* {user.username}\n"
                f"• *Role:* {role}\n"
                f"• *Notifications:* {'Enabled' if profile.notifications_enabled else 'Disabled'}"
            )
        except TelegramProfile.DoesNotExist:
            send_telegram_message(chat_id, "ℹ️ *Status: Unlinked*\n\nTo link your account, use `/login` or link from the website.")

    elif command == "/help":
        send_telegram_message(
            chat_id,
            "💡 *Available Commands:*\n\n"
            "• `/login <username> <password>` - Log in and link your TradeHub account\n"
            "• `/logout` - Unlink your account\n"
            "• `/status` - Check your link status and settings\n"
            "• `/help` - Show this help message"
        )
    else:
        # Fallback response
        send_telegram_message(
            chat_id,
            "❓ *Unknown Command.*\n"
            "Type `/help` to see the list of available commands."
        )
