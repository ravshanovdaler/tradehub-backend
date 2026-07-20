from django.contrib import admin
from .models import (
    Category, Product, ProductImage, ProductVariant, ProductReview, ProductView,
    ProductLike, SavedProduct, ProductDescriptionImage
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

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('icon', 'name_en', 'name_uz', 'name_ru', 'slug', 'product_count', 'created_at')
    list_display_links = ('name_en',)
    list_editable = ('name_uz', 'name_ru')
    search_fields = ('name_en', 'name_uz', 'name_ru', 'description')
    prepopulated_fields = {'slug': ('name_en',)}
    readonly_fields = ('created_at', 'name')
    fieldsets = (
        ('Names', {
            'fields': ('name_en', 'name_uz', 'name_ru'),
            'description': 'Enter the category name in each supported language. English is required.',
        }),
        ('Settings', {
            'fields': ('slug', 'icon', 'description'),
        }),
        ('Meta', {
            'fields': ('name', 'created_at'),
            'classes': ('collapse',),
            'description': 'Legacy field (auto-synced from English name)',
        }),
    )

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'seller', 'category', 'price', 'moq', 'views_count', 'created_at')
    list_filter = ('category', 'seller', 'created_at')
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
admin.site.register(ProductLike, ProductLikeAdmin)
admin.site.register(SavedProduct, SavedProductAdmin)
admin.site.register(ProductDescriptionImage)
