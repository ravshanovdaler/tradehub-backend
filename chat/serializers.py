from rest_framework import serializers
from .models import ChatRoom, ChatMessage
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatMessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    media_url = serializers.SerializerMethodField()
    order_status = serializers.SerializerMethodField()
    order_total_price = serializers.SerializerMethodField()

    def get_media_url(self, obj):
        if obj.media:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.media.url)
            return obj.media.url
        return None

    def get_order_status(self, obj):
        return obj.order.status if obj.order else None

    def get_order_total_price(self, obj):
        return float(obj.order.total_price) if obj.order else None

    class Meta:
        model = ChatMessage
        fields = ['id', 'room', 'sender', 'sender_username', 'message', 'media', 'media_url', 'order', 'order_status', 'order_total_price', 'is_read', 'timestamp']
        read_only_fields = ['sender', 'sender_username', 'timestamp']

class ChatRoomSerializer(serializers.ModelSerializer):
    buyer_username = serializers.CharField(source='buyer.username', read_only=True)
    seller_username = serializers.CharField(source='seller.username', read_only=True)
    seller_company = serializers.SerializerMethodField()
    seller_logo = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    last_message_timestamp = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    def get_seller_company(self, obj):
        try:
            return obj.seller.seller_profile.company_name
        except Exception:
            return obj.seller.username

    def get_last_message(self, obj):
        last = obj.messages.order_by('-timestamp').first()
        if not last:
            return ""
        if last.media:
            return "📁 [Media File]"
        if last.order_id:
            return "📦 [Order Proposal]"
        return last.message if last.message else ""

    def get_last_message_timestamp(self, obj):
        last = obj.messages.order_by('-timestamp').first()
        return last.timestamp.isoformat() if last else None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0
        return obj.messages.filter(is_read=False).exclude(sender=request.user).count()

    def get_seller_logo(self, obj):
        try:
            logo = obj.seller.seller_profile.company_logo
            if logo:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(logo.url)
                return f"http://127.0.0.1:8000{logo.url}"
            return None
        except Exception:
            return None

    class Meta:
        model = ChatRoom
        fields = [
            'id', 'buyer', 'buyer_username', 'seller', 'seller_username', 
            'seller_company', 'seller_logo', 'last_message', 'last_message_timestamp', 'unread_count', 'created_at'
        ]
        read_only_fields = ['buyer', 'created_at']
