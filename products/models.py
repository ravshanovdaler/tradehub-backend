from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Product(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    moq = models.IntegerField(default=1, verbose_name="Minimum Order Quantity")
    manufacturing_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    views_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/')

    def __str__(self):
        return f"Image for {self.product.name}"

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    attribute_name = models.CharField(max_length=50, help_text="e.g. Size, Color")
    attribute_value = models.CharField(max_length=50, help_text="e.g. L, XL, Blue, Red")
    additional_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.product.name} - {self.attribute_name}: {self.attribute_value}"

class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=5)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username} on {self.product.name}"

class ProductView(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='view_records')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"View of {self.product.name} at {self.timestamp}"


# ─── Comments (social-style, supports media & nested replies) ──────────────────

class ProductComment(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='product_comments')
    text = models.TextField(blank=True)
    # Optional media attachment (image or video)
    media = models.FileField(upload_to='comment_media/', null=True, blank=True)
    # Parent comment for nested replies (null = top-level comment)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.user.username} on {self.product.name}"


# ─── Likes ─────────────────────────────────────────────────────────────────────

class ProductLike(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='liked_products')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} likes {self.product.name}"


# ─── Saved / Bookmarked Products ───────────────────────────────────────────────

class SavedProduct(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-saved_at']

    def __str__(self):
        return f"{self.user.username} saved {self.product.name}"


class ProductDescriptionImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='description_images')
    image = models.ImageField(upload_to='product_description_images/')

    def __str__(self):
        return f"Description Image for {self.product.name}"

