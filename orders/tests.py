from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from orders.models import Order
from chat.models import ChatRoom, ChatMessage
from accounts.models import SellerProfile

User = get_user_model()

class OrderApprovalChatNotificationTestCase(APITestCase):
    def setUp(self):
        # Create seller and buyer
        self.seller = User.objects.create_user(
            username='seller_test',
            email='seller_test@test.com',
            password='password123',
            is_seller=True
        )
        self.seller_profile = SellerProfile.objects.create(
            user=self.seller,
            company_name='Test Factory LLC',
            business_address='123 Factory Rd',
            address_latitude=41.2995,
            address_longitude=69.2401,
            order_approve_message_template="Approved order #{order_id} for {buyer_name}. Price: ${total_price}, Transport: ${transport_cost}."
        )

        self.buyer = User.objects.create_user(
            username='buyer_test',
            email='buyer_test@test.com',
            password='password123',
            is_buyer=True
        )

        # Create a pending order
        self.order = Order.objects.create(
            seller=self.seller,
            buyer=self.buyer,
            total_price=1250.00,
            status='PENDING'
        )

        # Login as seller
        self.client.login(username='seller_test', password='password123')

    def test_approve_order_sends_templated_message(self):
        url = reverse('order-update-status', kwargs={'pk': self.order.id})
        payload = {
            'status': 'PACKAGING',
            'transport_cost': 75.00
        }
        
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Reload order
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'PACKAGING')
        self.assertEqual(float(self.order.transport_cost), 75.00)

        # Verify chat room was created/fetched
        room = ChatRoom.objects.filter(buyer=self.buyer, seller=self.seller).first()
        self.assertIsNotNone(room)

        # Verify message was sent with template content
        msg = ChatMessage.objects.filter(room=room).first()
        self.assertIsNotNone(msg)
        self.assertEqual(msg.sender, self.seller)
        
        expected_text = f"Approved order #{self.order.id} for buyer_test. Price: $1250.0, Transport: $75.0."
        self.assertEqual(msg.message, expected_text)

    def test_approve_order_fallback_on_invalid_template_variables(self):
        # Update template to have an invalid placeholder
        self.seller_profile.order_approve_message_template = "Invalid template tag {non_existent_field}"
        self.seller_profile.save()

        url = reverse('order-update-status', kwargs={'pk': self.order.id})
        payload = {
            'status': 'PACKAGING',
            'transport_cost': 45.00
        }
        
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify message fell back gracefully
        room = ChatRoom.objects.filter(buyer=self.buyer, seller=self.seller).first()
        msg = ChatMessage.objects.filter(room=room).first()
        self.assertIsNotNone(msg)
        
        # Verify fallback message structure
        self.assertIn("approved", msg.message.lower())
        self.assertIn(str(self.order.id), msg.message)
        self.assertIn("45.0", msg.message)

    def test_approve_order_uses_default_when_template_empty(self):
        # Clear template
        self.seller_profile.order_approve_message_template = ""
        self.seller_profile.save()

        url = reverse('order-update-status', kwargs={'pk': self.order.id})
        payload = {
            'status': 'PACKAGING',
            'transport_cost': 100.00
        }
        
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify message was sent with default template
        room = ChatRoom.objects.filter(buyer=self.buyer, seller=self.seller).first()
        msg = ChatMessage.objects.filter(room=room).first()
        self.assertIsNotNone(msg)
        self.assertIn("Hello! I have approved your order", msg.message)
        self.assertIn("100.0", msg.message)
