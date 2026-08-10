import secrets
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import TelegramProfile
from .bot_logic import handle_telegram_message

class TelegramStatusView(APIView):
    """Retrieves the Telegram linking status of the authenticated user."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        profile, _ = TelegramProfile.objects.get_or_create(user=request.user)
        return Response({
            'linked': profile.chat_id is not None,
            'chat_id': profile.chat_id,
            'notifications_enabled': profile.notifications_enabled,
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
    """Receives real-time update notifications from Telegram Bot API."""
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
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error handling Telegram webhook message: {e}")
        
        return Response({"status": "ok"}, status=status.HTTP_200_OK)
