from django.db import models
from django.conf import settings

class TelegramProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='telegram_profile')
    chat_id = models.CharField(max_length=100, unique=True, blank=True, null=True)
    auth_token = models.CharField(max_length=64, unique=True, blank=True, null=True)
    notifications_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.chat_id or 'Not linked'}"
