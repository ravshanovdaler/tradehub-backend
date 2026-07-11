from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from django.db.models import Count, Sum, Q
from .models import (
    Product, ProductImage, ProductVariant, ProductReview, ProductView,
    ProductLike, SavedProduct, ProductDescriptionImage, Category
)
from .serializers import (
    ProductSerializer, ProductImageSerializer, ProductVariantSerializer,
    ProductReviewSerializer, ProductLikeSerializer,
    SavedProductSerializer, ProductDescriptionImageSerializer, CategorySerializer
)
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser


class IsAdminOrReadOnly(permissions.BasePermission):
    """Admin users can write; everyone else can only read."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and request.user.is_staff


class CategoryViewSet(viewsets.ModelViewSet):
    """Categories: read-only for all, write for admin only."""
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'


class IsSellerAndVerified(permissions.BasePermission):
    """Only verified sellers can create/update/delete products.
    Anyone (including anonymous) can read (GET, HEAD, OPTIONS)."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        return (
            request.user.is_seller and
            hasattr(request.user, 'seller_profile') and
            request.user.seller_profile.is_verified
        )

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.seller == request.user


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsSellerAndVerified]

    # ── Search & Ordering ────────────────────────────────────────────────────
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    # Search: partial/fuzzy match on name and description
    search_fields = ['name', 'description']
    # Ordering: expose these fields for ?ordering= param
    ordering_fields = ['price', 'views_count', 'likes_count_ann', 'total_orders_ann', 'created_at']
    ordering = ['-created_at']  # default ordering

    def get_queryset(self):
        """Annotate queryset with likes_count and total_orders for sorting/display."""
        queryset = Product.objects.all().annotate(
            likes_count_ann=Count('likes', distinct=True),
            total_orders_ann=Count('orderitem__order', distinct=True, filter=~Q(orderitem__order__status__in=['PENDING', 'CANCELLED'])),
        ).order_by('-created_at')
        
        seller_id = self.request.query_params.get('seller')
        if seller_id:
            queryset = queryset.filter(seller_id=seller_id)

        category_slug = self.request.query_params.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        # Increment view count and record view atomically
        with transaction.atomic():
            instance.views_count += 1
            instance.save(update_fields=['views_count'])

            user = request.user if (request.user and request.user.is_authenticated) else None
            ProductView.objects.create(product=instance, user=user)

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    # ── Image Upload ──────────────────────────────────────────────────────────

    @action(detail=True, methods=['POST'], permission_classes=[permissions.IsAuthenticated],
            parser_classes=[MultiPartParser, FormParser])
    def upload_image(self, request, pk=None):
        product = self.get_object()
        if product.seller != request.user:
            return Response({'error': 'You do not own this product.'}, status=status.HTTP_403_FORBIDDEN)

        image_file = request.FILES.get('image')
        if not image_file:
            return Response({'error': 'No image provided.'}, status=status.HTTP_400_BAD_REQUEST)

        img_obj = ProductImage.objects.create(product=product, image=image_file)
        serializer = ProductImageSerializer(img_obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['POST'], permission_classes=[permissions.IsAuthenticated],
            parser_classes=[MultiPartParser, FormParser])
    def upload_description_image(self, request, pk=None):
        product = self.get_object()
        if product.seller != request.user:
            return Response({'error': 'You do not own this product.'}, status=status.HTTP_403_FORBIDDEN)

        image_file = request.FILES.get('image')
        if not image_file:
            return Response({'error': 'No image provided.'}, status=status.HTTP_400_BAD_REQUEST)

        img_obj = ProductDescriptionImage.objects.create(product=product, image=image_file)
        serializer = ProductDescriptionImageSerializer(img_obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['DELETE'], permission_classes=[permissions.IsAuthenticated],
            url_path=r'delete_image/(?P<image_id>\d+)')
    def delete_image(self, request, pk=None, image_id=None):
        product = self.get_object()
        if product.seller != request.user:
            return Response({'error': 'You do not own this product.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            img = ProductImage.objects.get(id=image_id, product=product)
            img.delete()
            return Response({'message': 'Image deleted successfully.'}, status=status.HTTP_200_OK)
        except ProductImage.DoesNotExist:
            return Response({'error': 'Image not found.'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['DELETE'], permission_classes=[permissions.IsAuthenticated],
            url_path=r'delete_description_image/(?P<image_id>\d+)')
    def delete_description_image(self, request, pk=None, image_id=None):
        product = self.get_object()
        if product.seller != request.user:
            return Response({'error': 'You do not own this product.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            img = ProductDescriptionImage.objects.get(id=image_id, product=product)
            img.delete()
            return Response({'message': 'Description image deleted successfully.'}, status=status.HTTP_200_OK)
        except ProductDescriptionImage.DoesNotExist:
            return Response({'error': 'Image not found.'}, status=status.HTTP_404_NOT_FOUND)


    # ── Variants ──────────────────────────────────────────────────────────────

    @action(detail=True, methods=['POST'], permission_classes=[permissions.IsAuthenticated])
    def add_variant(self, request, pk=None):
        product = self.get_object()
        if product.seller != request.user:
            return Response({'error': 'You do not own this product.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = ProductVariantSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(product=product)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['DELETE'], permission_classes=[permissions.IsAuthenticated],
            url_path=r'delete_variant/(?P<variant_id>\d+)')
    def delete_variant(self, request, pk=None, variant_id=None):
        product = self.get_object()
        if product.seller != request.user:
            return Response({'error': 'You do not own this product.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            var_obj = ProductVariant.objects.get(id=variant_id, product=product)
            var_obj.delete()
            return Response({'message': 'Variant deleted successfully.'}, status=status.HTTP_200_OK)
        except ProductVariant.DoesNotExist:
            return Response({'error': 'Variant not found.'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['PUT', 'PATCH'], permission_classes=[permissions.IsAuthenticated],
            url_path=r'update_variant/(?P<variant_id>\d+)')
    def update_variant(self, request, pk=None, variant_id=None):
        product = self.get_object()
        if product.seller != request.user:
            return Response({'error': 'You do not own this product.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            var_obj = ProductVariant.objects.get(id=variant_id, product=product)
            serializer = ProductVariantSerializer(var_obj, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ProductVariant.DoesNotExist:
            return Response({'error': 'Variant not found.'}, status=status.HTTP_404_NOT_FOUND)


    # ── Reviews ───────────────────────────────────────────────────────────────

    @action(detail=True, methods=['POST'], permission_classes=[permissions.IsAuthenticated],
            parser_classes=[JSONParser, MultiPartParser, FormParser])
    def add_review(self, request, pk=None):
        product = self.get_object()
        parent_id = request.data.get('parent')

        parent = None
        if parent_id:
            try:
                parent = ProductReview.objects.get(id=parent_id, product=product)
            except ProductReview.DoesNotExist:
                return Response({'error': 'Parent review not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not parent:
            # Top-level review. Only buyers can review.
            if not request.user.is_buyer:
                return Response({'error': 'Only buyers can leave reviews.'}, status=status.HTTP_403_FORBIDDEN)
        else:
            # Reply review. Only manufacturer of this product can reply.
            if product.seller != request.user:
                return Response({'error': 'Only the manufacturer can reply to reviews on this product.'}, status=status.HTTP_403_FORBIDDEN)

        rating = request.data.get('rating')
        if rating is not None:
            try:
                rating = int(rating)
            except ValueError:
                rating = 5
        elif not parent:
            rating = 5
        else:
            rating = None

        comment = request.data.get('comment', '').strip()
        media_file = request.FILES.get('media')

        if not comment and not media_file:
            return Response({'error': 'Review must have comment text or media.'}, status=status.HTTP_400_BAD_REQUEST)

        review = ProductReview.objects.create(
            product=product,
            user=request.user,
            rating=rating,
            comment=comment,
            media=media_file,
            parent=parent
        )
        serializer = ProductReviewSerializer(review, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # ── Likes ─────────────────────────────────────────────────────────────────

    @action(detail=True, methods=['POST'], permission_classes=[permissions.IsAuthenticated])
    def toggle_like(self, request, pk=None):
        """Toggle like on a product. Returns liked status and count."""
        product = self.get_object()
        like, created = ProductLike.objects.get_or_create(user=request.user, product=product)
        if not created:
            # Already liked → unlike it
            like.delete()
            liked = False
        else:
            liked = True

        likes_count = product.likes.count()
        return Response({
            'liked': liked,
            'likes_count': likes_count,
        }, status=status.HTTP_200_OK)

    # ── Save / Bookmark ───────────────────────────────────────────────────────

    @action(detail=True, methods=['POST'], permission_classes=[permissions.IsAuthenticated])
    def save_product(self, request, pk=None):
        """Toggle save/bookmark on a product."""
        product = self.get_object()
        saved_obj, created = SavedProduct.objects.get_or_create(user=request.user, product=product)
        if not created:
            # Already saved → unsave
            saved_obj.delete()
            return Response({'saved': False, 'message': 'Product removed from saved.'}, status=status.HTTP_200_OK)
        return Response({'saved': True, 'message': 'Product saved successfully.'}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['GET'], permission_classes=[permissions.IsAuthenticated])
    def my_saved(self, request):
        """List all products saved by the authenticated user."""
        saved = SavedProduct.objects.filter(user=request.user).select_related('product')
        serializer = SavedProductSerializer(saved, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['GET'], permission_classes=[permissions.IsAuthenticated])
    def my_liked(self, request):
        """List all products liked by the authenticated user."""
        liked_products = Product.objects.filter(likes__user=request.user)
        serializer = self.get_serializer(liked_products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'], permission_classes=[permissions.IsAuthenticated])
    def my_reviews(self, request):
        """List all reviews written by the authenticated user."""
        from .models import ProductReview
        reviews = ProductReview.objects.filter(user=request.user).select_related('product')
        serializer = ProductReviewSerializer(reviews, many=True, context={'request': request})
        return Response(serializer.data)

    # ── Share ─────────────────────────────────────────────────────────────────

    @action(detail=True, methods=['GET'], permission_classes=[permissions.AllowAny])
    def share(self, request, pk=None):
        """Get a shareable link for a product."""
        product = self.get_object()
        # Build frontend URL — use request origin or fallback
        origin = request.META.get('HTTP_ORIGIN', 'http://localhost:3000')
        share_url = f"{origin}/products/{product.id}"
        return Response({
            'share_url': share_url,
            'product_id': product.id,
            'product_name': product.name,
        }, status=status.HTTP_200_OK)
