from django.contrib import admin
from .models import Order, OrderItem, OrderLocation

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1

class OrderLocationInline(admin.TabularInline):
    model = OrderLocation
    extra = 1

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer', 'seller', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('buyer__username', 'seller__username')
    inlines = [OrderItemInline, OrderLocationInline]

admin.site.register(Order, OrderAdmin)
