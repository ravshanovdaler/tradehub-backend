from django.urls import path
from .views import (
    TelegramStatusView,
    TelegramLanguageView,
    TelegramGenerateLinkView,
    TelegramUnlinkView,
    TelegramWebhookView
)

urlpatterns = [
    path('status/', TelegramStatusView.as_view(), name='telegram_status'),
    path('language/', TelegramLanguageView.as_view(), name='telegram_language'),
    path('link/', TelegramGenerateLinkView.as_view(), name='telegram_link'),
    path('unlink/', TelegramUnlinkView.as_view(), name='telegram_unlink'),
    path('webhook/', TelegramWebhookView.as_view(), name='telegram_webhook'),
]
