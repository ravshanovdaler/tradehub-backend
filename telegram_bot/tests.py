from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from telegram_bot.models import TelegramProfile
from orders.models import Order
from chat.models import ChatRoom, ChatMessage

User = get_user_model()

class TelegramBotTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
            email="testuser@example.com",
            first_name="Test",
            last_name="User"
        )
        self.client.force_authenticate(user=self.user)

    def test_get_telegram_status_unlinked(self):
        url = reverse('telegram_status')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['linked'])
        self.assertIsNone(response.data['chat_id'])

    def test_generate_telegram_link(self):
        url = reverse('telegram_link')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('bot_url', response.data)
        
        # Verify db profile
        profile = TelegramProfile.objects.get(user=self.user)
        self.assertEqual(profile.auth_token, response.data['token'])

    def test_unlink_telegram(self):
        profile = TelegramProfile.objects.create(user=self.user, chat_id="123456")
        url = reverse('telegram_unlink')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        profile.refresh_from_db()
        self.assertIsNone(profile.chat_id)

    @patch('urllib.request.urlopen')
    def test_webhook_linking(self, mock_urlopen):
        # Setup mock response for Telegram api message confirmation
        mock_urlopen.return_value.__enter__.return_value.read.return_value = b'{"ok": true, "result": {}}'
        
        # Generate token
        profile = TelegramProfile.objects.create(user=self.user, auth_token="mytoken123")
        
        # Call Webhook
        url = reverse('telegram_webhook')
        payload = {
            "update_id": 10000,
            "message": {
                "message_id": 1,
                "chat": {"id": 999888, "type": "private"},
                "text": "/start mytoken123",
                "from": {"username": "testtguser"}
            }
        }
        
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Profile should be linked
        profile.refresh_from_db()
        self.assertEqual(profile.chat_id, "999888")
        self.assertIsNone(profile.auth_token)

    @patch('telegram_bot.utils.send_telegram_message')
    def test_signals_order_created(self, mock_send_message):
        seller = User.objects.create_user(username="seller", password="pwd", is_seller=True)
        TelegramProfile.objects.create(user=seller, chat_id="999")
        
        # Create order
        Order.objects.create(
            buyer=self.user,
            seller=seller,
            total_price=150.00,
            currency="USD",
            status="PENDING"
        )
        
        # Signal post_save on Order should invoke send_telegram_message
        import time
        time.sleep(0.1)
        
        mock_send_message.assert_called_once()
        args, kwargs = mock_send_message.call_args
        self.assertEqual(args[0], "999")
        self.assertIn("New Sale", args[1])
