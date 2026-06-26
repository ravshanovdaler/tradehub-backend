from django.contrib import admin
from .models import (
    Product, ProductImage, ProductVariant, ProductReview, ProductView,
    ProductComment, ProductLike, SavedProduct, ProductDescriptionImage
)

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductDescriptionImageInline(admin.TabularInline):
    model = ProductDescriptionImage
    extra = 1

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'seller', 'price', 'moq', 'views_count', 'created_at')
    list_filter = ('seller', 'created_at')
    search_fields = ('name', 'description', 'seller__username')
    inlines = [ProductImageInline, ProductDescriptionImageInline, ProductVariantInline]


class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('comment', 'product__name', 'user__username')

class ProductViewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('product__name', 'user__username')

class ProductCommentAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'text', 'parent', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('text', 'product__name', 'user__username')
    raw_id_fields = ('parent',)

class ProductLikeAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('product__name', 'user__username')

class SavedProductAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'saved_at')
    list_filter = ('saved_at',)
    search_fields = ('product__name', 'user__username')

admin.site.register(Product, ProductAdmin)
admin.site.register(ProductReview, ProductReviewAdmin)
admin.site.register(ProductView, ProductViewAdmin)
admin.site.register(ProductComment, ProductCommentAdmin)
admin.site.register(ProductLike, ProductLikeAdmin)
admin.site.register(SavedProduct, SavedProductAdmin)
admin.site.register(ProductDescriptionImage)

