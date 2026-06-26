from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Order, OrderLocation
from .serializers import OrderSerializer, OrderLocationSerializer

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_seller:
            return Order.objects.filter(seller=user).order_by('-created_at')
        return Order.objects.filter(buyer=user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['POST'], permission_classes=[permissions.IsAuthenticated])
    def update_status(self, request, pk=None):
        order = self.get_object()
        if order.seller != request.user:
            return Response({'error': 'Only the manufacturer/seller of this order can update the status.'}, status=status.HTTP_403_FORBIDDEN)
            
        new_status = request.data.get('status')
        valid_statuses = [choice[0] for choice in Order.STATUS_CHOICES]
        if not new_status or new_status not in valid_statuses:
            return Response({'error': 'Invalid status choice. Valid values: ' + ', '.join(valid_statuses)}, status=status.HTTP_400_BAD_REQUEST)

        old_status = order.status
        order.status = new_status
        
        transport_cost = request.data.get('transport_cost')
        if transport_cost is not None:
            try:
                from decimal import Decimal
                tc_dec = Decimal(str(transport_cost))
                if tc_dec < 0:
                    return Response({'error': 'Transport cost must be non-negative.'}, status=status.HTTP_400_BAD_REQUEST)
                order.transport_cost = tc_dec
            except Exception:
                return Response({'error': 'Invalid transport cost value.'}, status=status.HTTP_400_BAD_REQUEST)

        order.save()

        # If order was confirmed (PENDING -> PACKAGING / other status), post automated chat message
        if old_status == 'PENDING' and new_status not in ['PENDING', 'CANCELLED']:
            from chat.models import ChatRoom, ChatMessage
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            room, _ = ChatRoom.objects.get_or_create(buyer=order.buyer, seller=order.seller)
            
            # Fetch template from seller profile
            seller_profile = getattr(order.seller, 'seller_profile', None)
            template = seller_profile.order_approve_message_template if seller_profile else ""
            if not template:
                template = "Hello! I have approved your order (Order #{order_id}). The transport cost is ${transport_cost}."
            
            try:
                msg_text = template.format(
                    order_id=order.id,
                    total_price=float(order.total_price),
                    transport_cost=float(order.transport_cost),
                    buyer_name=order.buyer.username
                )
            except Exception:
                msg_text = f"Hello! I have approved your order (Order #{order.id}). The transport cost is ${order.transport_cost}."

            msg = ChatMessage.objects.create(
                room=room,
                sender=order.seller,
                message=msg_text
            )

            # Notify websocket channel layer
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f'chat_{room.id}',
                    {
                        'type': 'chat_message',
                        'message_id': msg.id,
                        'message': msg.message,
                        'sender_id': msg.sender.id,
                        'sender_username': msg.sender.username,
                        'timestamp': msg.timestamp.isoformat()
                    }
                )

        # Automatically append a location status log
        description = f"Status updated to: {order.get_status_display()}"
        
        # Get coordinates from request data - no longer defaulting to Shanghai
        lat = request.data.get('latitude')
        lng = request.data.get('longitude')
        
        if lat is None or lng is None:
            seller_profile = getattr(order.seller, 'seller_profile', None)
            if seller_profile and seller_profile.address_latitude and seller_profile.address_longitude:
                lat = seller_profile.address_latitude
                lng = seller_profile.address_longitude
            else:
                lat = 41.2995
                lng = 69.2401

        desc_custom = request.data.get('description', description)

        OrderLocation.objects.create(
            order=order,
            latitude=lat,
            longitude=lng,
            description=desc_custom
        )

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST'], permission_classes=[permissions.IsAuthenticated])
    def add_location(self, request, pk=None):
        order = self.get_object()
        if order.seller != request.user:
            return Response({'error': 'Only the manufacturer/seller can update shipping coordinates.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = OrderLocationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(order=order)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
