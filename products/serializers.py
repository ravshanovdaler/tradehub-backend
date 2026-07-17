from rest_framework import serializers
from .models import Product, ProductImage, ProductVariant, ProductReview, ProductLike, SavedProduct, ProductDescriptionImage, Category
from accounts.utils import convert_currency


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()

    def get_product_count(self, obj):
        return obj.products.count()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon', 'description', 'product_count']


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
        fields = ['id', 'attribute_name', 'attribute_value', 'additional_price', 'additional_manufacturing_cost']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        request = self.context.get('request')
        target_currency = 'UZS'
        if request and request.user and request.user.is_authenticated:
            target_currency = getattr(request.user, 'currency', 'UZS')
        else:
            target_currency = getattr(instance.product, 'currency', 'UZS')
        
        product_currency = getattr(instance.product, 'currency', 'UZS')
        if 'additional_price' in ret and ret['additional_price'] is not None:
            ret['additional_price'] = convert_currency(float(ret['additional_price']), product_currency, target_currency)
        if 'additional_manufacturing_cost' in ret and ret['additional_manufacturing_cost'] is not None:
            ret['additional_manufacturing_cost'] = convert_currency(float(ret['additional_manufacturing_cost']), product_currency, target_currency)
        return ret


class ProductReviewSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    media_url = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()

    def get_media_url(self, obj):
        request = self.context.get('request')
        if obj.media and request:
            return request.build_absolute_uri(obj.media.url)
        return None

    def get_replies(self, obj):
        if obj.parent_id is not None:
            return []
        replies = obj.replies.all()
        return ProductReviewSerializer(replies, many=True, context=self.context).data

    class Meta:
        model = ProductReview
        fields = ['id', 'user', 'user_username', 'rating', 'comment', 'media_url', 'replies', 'parent', 'created_at']
        read_only_fields = ['user', 'user_username', 'created_at', 'replies']


class ProductLikeSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ProductLike
        fields = ['id', 'user', 'user_username', 'created_at']


# ─── Main Product Serializer ───────────────────────────────────────────────────

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    description_images = ProductDescriptionImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    reviews = serializers.SerializerMethodField()

    seller_company = serializers.SerializerMethodField()
    seller_username = serializers.CharField(source='seller.username', read_only=True)
    seller_logo = serializers.SerializerMethodField()
    is_seller_verified = serializers.SerializerMethodField()
    # Annotated fields (from queryset annotations)
    likes_count_ann = serializers.SerializerMethodField()
    total_orders_ann = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    # Category fields
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True, allow_null=True)
    category_icon = serializers.CharField(source='category.icon', read_only=True, allow_null=True)

    def get_reviews(self, obj):
        # Fetch only top-level reviews (parent=None)
        reviews = obj.reviews.filter(parent=None)
        return ProductReviewSerializer(reviews, many=True, context=self.context).data

    def get_seller_company(self, obj):
        try:
            return obj.seller.seller_profile.company_name
        except Exception:
            return None

    def get_is_seller_verified(self, obj):
        try:
            return obj.seller.seller_profile.is_verified
        except Exception:
            return False

    def get_likes_count_ann(self, obj):
        # Use annotation if available, else count directly
        if hasattr(obj, 'likes_count_ann'):
            return obj.likes_count_ann
        return obj.likes.count()

    def get_total_orders_ann(self, obj):
        if hasattr(obj, 'total_orders_ann'):
            return obj.total_orders_ann or 0
        from orders.models import OrderItem
        return OrderItem.objects.filter(
            product=obj
        ).exclude(
            order__status__in=['PENDING', 'CANCELLED']
        ).values('order').distinct().count()

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False

    def get_is_saved(self, obj):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            return obj.saved_by.filter(user=request.user).exists()
        return False

    def get_seller_logo(self, obj):
        try:
            logo = obj.seller.seller_profile.company_logo
            if logo:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(logo.url)
                return logo.url
            return None
        except Exception:
            return None

    class Meta:
        model = Product
        fields = [
            'id', 'seller', 'seller_company', 'seller_username', 'seller_logo',
            'is_seller_verified',
            'category', 'category_name', 'category_slug', 'category_icon',
            'name', 'description', 'price', 'currency', 'moq', 'manufacturing_cost',
            'views_count', 'likes_count_ann', 'total_orders_ann',
            'is_liked', 'is_saved',
            'images', 'description_images', 'variants', 'reviews', 'created_at'
        ]
        read_only_fields = ['seller', 'views_count', 'created_at']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        request = self.context.get('request')
        target_currency = 'UZS'
        if request and request.user and request.user.is_authenticated:
            target_currency = getattr(request.user, 'currency', 'UZS')
        else:
            # If guest, default to the product's original currency
            target_currency = getattr(instance, 'currency', 'UZS')
        
        product_currency = getattr(instance, 'currency', 'UZS')
        
        if 'price' in ret and ret['price'] is not None:
            ret['price'] = convert_currency(float(ret['price']), product_currency, target_currency)
        if 'manufacturing_cost' in ret and ret['manufacturing_cost'] is not None:
            ret['manufacturing_cost'] = convert_currency(float(ret['manufacturing_cost']), product_currency, target_currency)
            
        ret['currency'] = target_currency
        return ret

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data['currency'] = getattr(request.user, 'currency', 'UZS')
        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data['currency'] = getattr(request.user, 'currency', 'UZS')
        return super().update(instance, validated_data)


# ─── Saved Products ────────────────────────────────────────────────────────────

class SavedProductSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = SavedProduct
        fields = ['id', 'product', 'saved_at']
        read_only_fields = ['saved_at']
