from rest_framework import serializers
from .models import ChatRoom, ChatMessage
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatMessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)

    class Meta:
        model = ChatMessage
        fields = ['id', 'room', 'sender', 'sender_username', 'message', 'timestamp']
        read_only_fields = ['sender', 'sender_username', 'timestamp']

class ChatRoomSerializer(serializers.ModelSerializer):
    buyer_username = serializers.CharField(source='buyer.username', read_only=True)
    seller_username = serializers.CharField(source='seller.username', read_only=True)
    seller_company = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    last_message_timestamp = serializers.SerializerMethodField()

    def get_seller_company(self, obj):
        try:
            return obj.seller.seller_profile.company_name
        except Exception:
            return obj.seller.username

    def get_last_message(self, obj):
        last = obj.messages.order_by('-timestamp').first()
        return last.message if last else ""

    def get_last_message_timestamp(self, obj):
        last = obj.messages.order_by('-timestamp').first()
        return last.timestamp.isoformat() if last else None

    class Meta:
        model = ChatRoom
        fields = [
            'id', 'buyer', 'buyer_username', 'seller', 'seller_username', 
            'seller_company', 'last_message', 'last_message_timestamp', 'created_at'
        ]
        read_only_fields = ['buyer', 'created_at']
