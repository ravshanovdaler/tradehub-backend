from rest_framework import serializers
from .models import Order, OrderItem, OrderLocation
from products.models import Product
from accounts.utils import convert_currency

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_moq = serializers.IntegerField(source='product.moq', read_only=True)
    selected_variant_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False, default=list
    )

    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_name', 'product_moq', 'quantity', 'price', 'manufacturing_cost',
            'selected_variant_ids', 'selected_variants_info'
        ]
        read_only_fields = ['price', 'manufacturing_cost', 'selected_variants_info']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        request = self.context.get('request')
        target_currency = 'UZS'
        if request and request.user and request.user.is_authenticated:
            target_currency = getattr(request.user, 'currency', 'UZS')
            
        order_currency = getattr(instance.order, 'currency', 'UZS')
        if 'price' in ret and ret['price'] is not None:
            ret['price'] = convert_currency(float(ret['price']), order_currency, target_currency)
        if 'manufacturing_cost' in ret and ret['manufacturing_cost'] is not None:
            ret['manufacturing_cost'] = convert_currency(float(ret['manufacturing_cost']), order_currency, target_currency)
        return ret

class OrderLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderLocation
        fields = ['id', 'latitude', 'longitude', 'description', 'timestamp']
        read_only_fields = ['timestamp']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    locations = OrderLocationSerializer(many=True, read_only=True)
    buyer_username = serializers.CharField(source='buyer.username', read_only=True)
    buyer_delivery_address = serializers.SerializerMethodField()
    buyer_phone = serializers.CharField(source='buyer.phone_number', read_only=True)
    seller_company = serializers.SerializerMethodField()

    def get_seller_company(self, obj):
        try:
            return obj.seller.seller_profile.company_name
        except Exception:
            return obj.seller.username

    def get_buyer_delivery_address(self, obj):
        try:
            return obj.buyer.buyer_profile.delivery_address
        except Exception:
            return ""

    class Meta:
        model = Order
        fields = [
            'id', 'buyer', 'buyer_username', 'buyer_delivery_address', 'buyer_phone',
            'seller', 'seller_company', 'status', 'total_price', 'transport_cost', 'currency',
            'items', 'locations', 'created_at', 'updated_at'
        ]
        read_only_fields = ['buyer', 'seller', 'buyer_username', 'buyer_delivery_address', 'buyer_phone', 'seller_company', 'total_price', 'created_at', 'updated_at']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        request = self.context.get('request')
        target_currency = 'UZS'
        if request and request.user and request.user.is_authenticated:
            target_currency = getattr(request.user, 'currency', 'UZS')
            
        order_currency = getattr(instance, 'currency', 'UZS')
        if 'total_price' in ret and ret['total_price'] is not None:
            ret['total_price'] = convert_currency(float(ret['total_price']), order_currency, target_currency)
        if 'transport_cost' in ret and ret['transport_cost'] is not None:
            ret['transport_cost'] = convert_currency(float(ret['transport_cost']), order_currency, target_currency)
            
        ret['currency'] = target_currency
        return ret

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        creator = self.context['request'].user

        if not items_data:
            raise serializers.ValidationError("An order must have at least one product item.")

        if creator.is_buyer:
            buyer = creator
            first_product = items_data[0]['product']
            seller = first_product.seller
        else:
            # Creator is seller. Check for buyer in request data.
            buyer_id = self.context['request'].data.get('buyer')
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                buyer = User.objects.get(id=buyer_id, is_buyer=True)
            except User.DoesNotExist:
                raise serializers.ValidationError("Valid buyer ID must be specified for seller-created orders.")
            seller = creator
        
        for item in items_data:
            if item['product'].seller != seller:
                raise serializers.ValidationError("All products in a single order must belong to the same manufacturer.")
            if item['quantity'] < item['product'].moq:
                raise serializers.ValidationError(f"Quantity for {item['product'].name} must be at least the MOQ of {item['product'].moq}.")

        total_price = 0
        order_items_to_create = []

        for item_data in items_data:
            product = item_data['product']
            quantity = item_data['quantity']
            variant_ids = item_data.get('selected_variant_ids', [])
            
            unit_price = product.price
            unit_mfg_cost = product.manufacturing_cost
            variant_desc_parts = []
            
            if variant_ids:
                from products.models import ProductVariant
                variants = ProductVariant.objects.filter(id__in=variant_ids, product=product)
                for var in variants:
                    unit_price += var.additional_price
                    unit_mfg_cost += var.additional_manufacturing_cost
                    variant_desc_parts.append(f"{var.attribute_name}: {var.attribute_value}")
                    
            selected_info = ", ".join(variant_desc_parts)
            total_price += unit_price * quantity
            order_items_to_create.append((product, quantity, unit_price, unit_mfg_cost, selected_info))

        order = Order.objects.create(buyer=buyer, seller=seller, total_price=total_price, status='PENDING', currency=first_product.currency)

        for product, quantity, price, mfg_cost, selected_info in order_items_to_create:
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=price,
                manufacturing_cost=mfg_cost,
                selected_variants_info=selected_info
            )

        # Seed initial location status using seller factory coordinates
        seller_profile = getattr(seller, 'seller_profile', None)
        lat = seller_profile.address_latitude if seller_profile and seller_profile.address_latitude else 41.2995
        lng = seller_profile.address_longitude if seller_profile and seller_profile.address_longitude else 69.2401

        OrderLocation.objects.create(
            order=order,
            latitude=lat,
            longitude=lng,
            description="Order Placed - Pending Manufacturer Confirmation"
        )

        # Send automated notification to chat
        try:
            buyer_profile = getattr(buyer, 'buyer_profile', None)
            template = buyer_profile.order_message_template if buyer_profile else ""
        except Exception:
            template = ""

        if not template:
            template = "Hello! I have placed an order (Order #{order_id}) for {quantity} unit(s) of {product_name}. Total price: ${total_price}. Please confirm my order."

        product_names_list = []
        for p, _, _, selected_info in order_items_to_create:
            if p:
                name_str = p.name
                if selected_info:
                    name_str += f" ({selected_info})"
                product_names_list.append(name_str)
        product_names = ", ".join(product_names_list)
        total_quantity = sum([qty for _, qty, _, _ in order_items_to_create])

        message_body = template.replace("{order_id}", str(order.id))\
                               .replace("{product_name}", product_names)\
                               .replace("{quantity}", str(total_quantity))\
                               .replace("{total_price}", f"{total_price:.2f}")

        try:
            from chat.models import ChatRoom, ChatMessage
            room, created = ChatRoom.objects.get_or_create(buyer=buyer, seller=seller)
            
            # Create database message
            msg = ChatMessage.objects.create(
                room=room,
                sender=buyer,
                message=message_body,
                order=order
            )

            # Broadcast via WebSocket channel layer
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f'chat_{room.id}',
                    {
                        'type': 'chat_message',
                        'message_id': msg.id,
                        'message': msg.message,
                        'sender_id': buyer.id,
                        'sender_username': buyer.username,
                        'order_id': order.id,
                        'order_status': order.status,
                        'order_total_price': float(order.total_price),
                        'timestamp': msg.timestamp.isoformat()
                    }
                )
        except Exception as chat_err:
            print("Failed to auto-send order chat message:", chat_err)

        return order
