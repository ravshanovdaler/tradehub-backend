import secrets
import logging
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import TelegramProfile
from .bot_logic import handle_telegram_message, handle_telegram_callback_query

logger = logging.getLogger(__name__)

class TelegramStatusView(APIView):
    """Retrieves or updates the Telegram linking status and language of the authenticated user."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        profile, _ = TelegramProfile.objects.get_or_create(user=request.user)
        return Response({
            'linked': profile.chat_id is not None,
            'chat_id': profile.chat_id,
            'notifications_enabled': profile.notifications_enabled,
            'language': profile.language,
        })

    def patch(self, request, *args, **kwargs):
        profile, _ = TelegramProfile.objects.get_or_create(user=request.user)
        language = request.data.get('language')
        if language:
            if language not in ['en', 'ru', 'uz']:
                return Response({'error': 'Invalid language choice. Choose from: en, ru, uz.'}, status=status.HTTP_400_BAD_REQUEST)
            profile.language = language

        notifications_enabled = request.data.get('notifications_enabled')
        if notifications_enabled is not None:
            profile.notifications_enabled = bool(notifications_enabled)

        profile.save()
        return Response({
            'linked': profile.chat_id is not None,
            'chat_id': profile.chat_id,
            'notifications_enabled': profile.notifications_enabled,
            'language': profile.language,
        })

class TelegramLanguageView(APIView):
    """Updates the preferred language for the authenticated user's Telegram profile."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        language = request.data.get('language')
        if not language or language not in ['en', 'ru', 'uz']:
            return Response({'error': 'Invalid or missing language. Valid choices: en, ru, uz.'}, status=status.HTTP_400_BAD_REQUEST)

        profile, _ = TelegramProfile.objects.get_or_create(user=request.user)
        profile.language = language
        profile.save()
        return Response({
            'message': f'Language updated to {language}.',
            'language': profile.language
        })

class TelegramGenerateLinkView(APIView):
    """Generates a unique auth token and returns the Telegram bot start link."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        bot_username = getattr(settings, 'TELEGRAM_BOT_USERNAME', '')
        if not bot_username:
            return Response({'error': 'Telegram Bot username is not configured on the server.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        token = secrets.token_urlsafe(24)
        profile, _ = TelegramProfile.objects.get_or_create(user=request.user)
        profile.auth_token = token
        profile.save()

        bot_url = f"https://t.me/{bot_username}?start={token}"
        return Response({
            'token': token,
            'bot_url': bot_url
        })

class TelegramUnlinkView(APIView):
    """Unlinks the user's Telegram account."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        profile = getattr(request.user, 'telegram_profile', None)
        if profile:
            profile.chat_id = None
            profile.auth_token = None
            profile.save()
            return Response({'message': 'Telegram account successfully unlinked.'})
        return Response({'message': 'No Telegram account was linked.'})

@method_decorator(csrf_exempt, name='dispatch')
class TelegramWebhookView(APIView):
    """Receives real-time update notifications (messages and callback queries) from Telegram Bot API."""
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        data = request.data
        if "message" in data:
            message = data["message"]
            chat_id = message.get("chat", {}).get("id")
            text = message.get("text")
            if chat_id and text:
                try:
                    handle_telegram_message(chat_id, text)
                except Exception as e:
                    logger.error(f"Error handling Telegram webhook message: {e}")
        elif "callback_query" in data:
            try:
                handle_telegram_callback_query(data["callback_query"])
            except Exception as e:
                logger.error(f"Error handling Telegram webhook callback query: {e}")

        return Response({"status": "ok"}, status=status.HTTP_200_OK)
