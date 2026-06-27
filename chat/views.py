from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import ChatRoom, ChatMessage
from .serializers import ChatRoomSerializer, ChatMessageSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatRoomViewSet(viewsets.ModelViewSet):
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return ChatRoom.objects.filter(Q(buyer=user) | Q(seller=user)).order_by('-created_at')

    @action(detail=False, methods=['POST'])
    def get_or_create_room(self, request):
        seller_id = request.data.get('seller_id')
        if not seller_id:
            return Response({'error': 'seller_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        buyer = request.user
        if not buyer.is_buyer:
            return Response({'error': 'Only buyers can initiate chat rooms with sellers.'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            seller = User.objects.get(id=seller_id, is_seller=True)
        except User.DoesNotExist:
            return Response({'error': 'Seller not found.'}, status=status.HTTP_404_NOT_FOUND)

        room, created = ChatRoom.objects.get_or_create(buyer=buyer, seller=seller)
        serializer = self.get_serializer(room)
        return Response(serializer.data, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)

    @action(detail=True, methods=['GET'])
    def messages(self, request, pk=None):
        room = self.get_object()
        if room.buyer != request.user and room.seller != request.user:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
            
        messages = room.messages.all()
        serializer = ChatMessageSerializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'])
    def new_inquiries(self, request):
        user = request.user
        if not user.is_seller:
            return Response([])
            
        rooms = ChatRoom.objects.filter(seller=user)
        new_rooms = []
        for r in rooms:
            # Check if the seller has ever sent any message in this room
            seller_sent = r.messages.filter(sender=user).exists()
            # Check if the buyer has sent at least one message in this room
            buyer_sent = r.messages.filter(sender=r.buyer).exists()
            if not seller_sent and buyer_sent:
                new_rooms.append(r)
                
        serializer = self.get_serializer(new_rooms, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['POST'])
    def send_media(self, request, pk=None):
        room = self.get_object()
        if room.buyer != request.user and room.seller != request.user:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        
        media_file = request.FILES.get('media')
        if not media_file:
            return Response({'error': 'No media file provided.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create message with media
        msg = ChatMessage.objects.create(
            room=room,
            sender=request.user,
            message=request.data.get('message', ''),
            media=media_file
        )
        
        # Notify WebSocket channel layer
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'chat_{room.id}',
                {
                    'type': 'chat_message',
                    'message_id': msg.id,
                    'message': msg.message or '',
                    'media_url': request.build_absolute_uri(msg.media.url) if msg.media else None,
                    'sender_id': msg.sender.id,
                    'sender_username': msg.sender.username,
                    'timestamp': msg.timestamp.isoformat()
                }
            )
        
        serializer = ChatMessageSerializer(msg, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['POST'])
    def mark_as_read(self, request, pk=None):
        room = self.get_object()
        if room.buyer != request.user and room.seller != request.user:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        
        room.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
        return Response({'success': True})
