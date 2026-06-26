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
