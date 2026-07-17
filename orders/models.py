from django.db import models
from django.contrib.auth import get_user_model
from products.models import Product

User = get_user_model()

class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('RECEIVED', 'Received'),
        ('CANCELLED', 'Cancelled'),
    ]

    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('UZS', 'Uzbekistan Som'),
    ]

    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buyer_orders')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seller_orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    transport_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='UZS')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.buyer.username} -> {self.seller.username} ({self.status})"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=12, decimal_places=2)  # Price locked at purchase time
    selected_variants_info = models.TextField(blank=True, default='')

    def __str__(self):
        return f"{self.quantity} x {self.product.name if self.product else 'Deleted Product'} in Order #{self.order.id}"

class OrderLocation(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='locations')
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    description = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Location for Order #{self.order.id} at {self.timestamp}: {self.description}"
