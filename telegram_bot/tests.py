from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from telegram_bot.models import TelegramProfile
from telegram_bot.bot_logic import handle_telegram_message, handle_telegram_callback_query
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
        self.assertEqual(response.data['language'], 'en')

    def test_update_telegram_language_api(self):
        url = reverse('telegram_language')
        response = self.client.post(url, {'language': 'ru'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['language'], 'ru')

        profile = TelegramProfile.objects.get(user=self.user)
        self.assertEqual(profile.language, 'ru')

    def test_update_telegram_status_patch(self):
        url = reverse('telegram_status')
        response = self.client.patch(url, {'language': 'uz', 'notifications_enabled': False}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['language'], 'uz')
        self.assertFalse(response.data['notifications_enabled'])

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

    @patch('telegram_bot.bot_logic.send_telegram_message')
    def test_bot_language_command(self, mock_send_message):
        profile = TelegramProfile.objects.create(user=self.user, chat_id="555444", language="en")

        # Call /language ru
        handle_telegram_message("555444", "/language ru")

        profile.refresh_from_db()
        self.assertEqual(profile.language, "ru")
        mock_send_message.assert_called_once()
        args, kwargs = mock_send_message.call_args
        self.assertEqual(args[0], "555444")
        self.assertIn("Язык изменен на Русский", args[1])

    @patch('telegram_bot.bot_logic.send_telegram_message')
    @patch('telegram_bot.bot_logic.answer_telegram_callback')
    def test_bot_callback_query_language(self, mock_answer, mock_send_message):
        profile = TelegramProfile.objects.create(user=self.user, chat_id="777888", language="en")

        cb_query = {
            "id": "cb123",
            "data": "set_lang_uz",
            "message": {
                "chat": {"id": 777888}
            }
        }
        handle_telegram_callback_query(cb_query)

        profile.refresh_from_db()
        self.assertEqual(profile.language, "uz")
        mock_answer.assert_called_once_with("cb123")
        mock_send_message.assert_called_once()
        args, kwargs = mock_send_message.call_args
        self.assertEqual(args[0], "777888")
        self.assertIn("Til Oʻzbekchaga oʻzgartirildi", args[1])

    @patch('telegram_bot.utils.send_telegram_message')
    def test_signals_order_created_localized(self, mock_send_message):
        seller = User.objects.create_user(username="seller", password="pwd", is_seller=True)
        TelegramProfile.objects.create(user=seller, chat_id="999", language="ru")
        
        # Create order
        Order.objects.create(
            buyer=self.user,
            seller=seller,
            total_price=150.00,
            currency="USD",
            status="PENDING"
        )
        
        import time
        time.sleep(0.1)
        
        mock_send_message.assert_called_once()
        args, kwargs = mock_send_message.call_args
        self.assertEqual(args[0], "999")
        self.assertIn("Новая продажа!", args[1])
