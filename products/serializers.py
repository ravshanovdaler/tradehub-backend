from rest_framework import serializers
from .models import Product, ProductImage, ProductVariant, ProductReview, ProductComment, ProductLike, SavedProduct, ProductDescriptionImage



class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image']


class ProductDescriptionImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductDescriptionImage
        fields = ['id', 'image']



class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['id', 'attribute_name', 'attribute_value', 'additional_price']


class ProductReviewSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ProductReview
        fields = ['id', 'user', 'user_username', 'rating', 'comment', 'created_at']
        read_only_fields = ['user', 'user_username', 'created_at']


# ─── Comments ──────────────────────────────────────────────────────────────────

class ProductCommentReplySerializer(serializers.ModelSerializer):
    """Serializer for nested replies (one level deep)."""
    user_username = serializers.CharField(source='user.username', read_only=True)
    media_url = serializers.SerializerMethodField()

    def get_media_url(self, obj):
        request = self.context.get('request')
        if obj.media and request:
            return request.build_absolute_uri(obj.media.url)
        return None

    class Meta:
        model = ProductComment
        fields = ['id', 'user', 'user_username', 'text', 'media_url', 'created_at']
        read_only_fields = ['user', 'user_username', 'created_at']


class ProductCommentSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    replies = ProductCommentReplySerializer(many=True, read_only=True)
    media_url = serializers.SerializerMethodField()

    def get_media_url(self, obj):
        request = self.context.get('request')
        if obj.media and request:
            return request.build_absolute_uri(obj.media.url)
        return None

    class Meta:
        model = ProductComment
        fields = [
            'id', 'user', 'user_username', 'text', 'media_url',
            'parent', 'replies', 'created_at'
        ]
        read_only_fields = ['user', 'user_username', 'created_at', 'replies']


# ─── Likes ─────────────────────────────────────────────────────────────────────

class ProductLikeSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ProductLike
        fields = ['id', 'user', 'user_username', 'created_at']
        read_only_fields = ['user', 'user_username', 'created_at']


# ─── Saved Products ────────────────────────────────────────────────────────────

class SavedProductSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=12, decimal_places=2, read_only=True)
    product_images = serializers.SerializerMethodField()
    product_created_at = serializers.DateTimeField(source='product.created_at', read_only=True)

    def get_product_images(self, obj):
        request = self.context.get('request')
        images = obj.product.images.all()
        if request:
            return [request.build_absolute_uri(img.image.url) for img in images if img.image]
        return []

    class Meta:
        model = SavedProduct
        fields = ['id', 'product', 'product_name', 'product_price', 'product_images', 'product_created_at', 'saved_at']
        read_only_fields = ['saved_at']


# ─── Main Product Serializer ───────────────────────────────────────────────────

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    description_images = ProductDescriptionImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    reviews = ProductReviewSerializer(many=True, read_only=True)

    seller_company = serializers.SerializerMethodField()
    seller_username = serializers.CharField(source='seller.username', read_only=True)
    seller_logo = serializers.SerializerMethodField()
    # Annotated fields (from queryset annotations)
    likes_count = serializers.SerializerMethodField()
    total_orders = serializers.SerializerMethodField()
    is_liked_by_user = serializers.SerializerMethodField()
    is_saved_by_user = serializers.SerializerMethodField()

    def get_seller_company(self, obj):
        try:
            return obj.seller.seller_profile.company_name
        except Exception:
            return None

    def get_likes_count(self, obj):
        # Use annotation if available, else count directly
        if hasattr(obj, 'likes_count_ann'):
            return obj.likes_count_ann
        return obj.likes.count()

    def get_total_orders(self, obj):
        if hasattr(obj, 'total_orders_ann'):
            return obj.total_orders_ann or 0
        from orders.models import OrderItem
        return OrderItem.objects.filter(
            product=obj
        ).exclude(
            order__status__in=['PENDING', 'CANCELLED']
        ).values('order').distinct().count()

    def get_is_liked_by_user(self, obj):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False

    def get_is_saved_by_user(self, obj):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            return obj.saved_by.filter(user=request.user).exists()
        return False

    def get_seller_logo(self, obj):
        try:
            logo = obj.seller.seller_profile.company_logo
            return logo.url if logo else None
        except Exception:
            return None

    class Meta:
        model = Product
        fields = [
            'id', 'seller', 'seller_company', 'seller_username', 'seller_logo',
            'name', 'description', 'price', 'moq', 'manufacturing_cost',
            'views_count', 'likes_count', 'total_orders',
            'is_liked_by_user', 'is_saved_by_user',
            'images', 'description_images', 'variants', 'reviews', 'created_at'
        ]

        read_only_fields = ['seller', 'views_count', 'created_at']
