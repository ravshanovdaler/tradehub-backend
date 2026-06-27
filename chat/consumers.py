import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from .models import ChatRoom, ChatMessage
from urllib.parse import parse_qs

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'

        query_string = self.scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token_key = query_params.get('token', [None])[0]

        self.user = await self.get_user_from_token(token_key)
        if self.user is None or not self.user.is_authenticated:
            await self.close()
            return

        has_access = await self.user_has_room_access(self.user, self.room_id)
        if not has_access:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_text = text_data_json.get('message', '').strip()
            order_id = text_data_json.get('order_id', None)
            
            if not message_text and not order_id:
                return

            msg_obj = await self.save_message(self.user, self.room_id, message_text, order_id)
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message_id': msg_obj['id'],
                    'message': msg_obj['message'],
                    'media_url': msg_obj['media_url'],
                    'order_id': msg_obj['order_id'],
                    'order_status': msg_obj['order_status'],
                    'order_total_price': msg_obj['order_total_price'],
                    'sender_id': msg_obj['sender_id'],
                    'sender_username': msg_obj['sender_username'],
                    'timestamp': msg_obj['timestamp']
                }
            )
        except Exception as e:
            await self.send(text_data=json.dumps({'error': str(e)}))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'id': event['message_id'],
            'message': event['message'],
            'media_url': event.get('media_url'),
            'order_id': event.get('order_id'),
            'order_status': event.get('order_status'),
            'order_total_price': event.get('order_total_price'),
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'timestamp': event['timestamp']
        }))

    @database_sync_to_async
    def get_user_from_token(self, token_key):
        if not token_key:
            return None
        try:
            token = Token.objects.select_related('user').get(key=token_key)
            return token.user
        except Token.DoesNotExist:
            return None

    @database_sync_to_async
    def user_has_room_access(self, user, room_id):
        try:
            room = ChatRoom.objects.get(id=room_id)
            return room.buyer == user or room.seller == user
        except ChatRoom.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, user, room_id, text, order_id=None):
        room = ChatRoom.objects.get(id=room_id)
        from orders.models import Order
        order = Order.objects.get(id=order_id) if order_id else None
        msg = ChatMessage.objects.create(
            room=room,
            sender=user,
            message=text,
            order=order
        )
        return {
            'id': msg.id,
            'message': msg.message or '',
            'media_url': msg.media.url if msg.media else None,
            'order_id': msg.order.id if msg.order else None,
            'order_status': msg.order.status if msg.order else None,
            'order_total_price': float(msg.order.total_price) if msg.order else None,
            'sender_id': msg.sender.id,
            'sender_username': msg.sender.username,
            'timestamp': msg.timestamp.isoformat()
        }
