from django.db import models
from django.contrib.auth.models import AbstractUser
import random
import string


def generate_otp():
    return ''.join(random.choices(string.digits, k=6))


class User(AbstractUser):
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('UZS', 'Uzbekistan Som'),
    ]

    is_seller = models.BooleanField(default=False)
    is_buyer = models.BooleanField(default=False)

    # Extended required fields (both roles)
    first_name = models.CharField(max_length=150, blank=False)
    last_name = models.CharField(max_length=150, blank=False)
    phone_number = models.CharField(max_length=20, blank=True, default='')
    additional_phone = models.CharField(max_length=20, blank=True, null=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='UZS')

    # Email verification
    email_verified = models.BooleanField(default=False)
    email_otp = models.CharField(max_length=6, blank=True, null=True)

    # Deletion requests
    deletion_requested = models.BooleanField(default=False)
    deletion_requested_at = models.DateTimeField(null=True, blank=True)

    # Privacy & Policy agreement (stored for compliance)
    agreed_to_privacy_policy = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} ({'Seller' if self.is_seller else 'Buyer' if self.is_buyer else 'Staff'})"


class PendingUser(models.Model):
    email = models.EmailField(unique=True)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    registration_data = models.JSONField(default=dict)

    def __str__(self):
        return f"PendingUser({self.email})"



class SellerDeletionRequest(User):
    class Meta:
        proxy = True
        verbose_name = "Seller Deletion Request"
        verbose_name_plural = "Seller Deletion Requests"






class SellerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='seller_profile')
    company_name = models.CharField(max_length=255)
    # Factory/warehouse address with coordinates for autofind
    business_address = models.TextField()
    address_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    address_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    registration_number = models.CharField(max_length=100)
    doc_file = models.FileField(upload_to='manufacturer_docs/', blank=True, null=True)
    business_doc = models.FileField(upload_to='business_docs/', blank=True, null=True)   # from registration
    passport_image = models.FileField(upload_to='seller_passports/', blank=True, null=True)  # ID doc
    company_logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    verification_notes = models.TextField(blank=True, null=True)
    
    quick_replies = models.TextField(blank=True, default='')
    company_description = models.TextField(blank=True, default='')
    order_approve_message_template = models.TextField(blank=True, default='')

    def __str__(self):
        return f"{self.company_name} - Verified: {self.is_verified}"


class UnverifiedSeller(SellerProfile):
    class Meta:
        proxy = True
        verbose_name = "Unverified Seller"
        verbose_name_plural = "Unverified Sellers"


class CompanyLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='liked_companies')
    company = models.ForeignKey(SellerProfile, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'company')

    def __str__(self):
        return f"{self.user.username} likes {self.company.company_name}"



class BuyerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='buyer_profile')
    # Delivery or pickup address
    delivery_address = models.TextField(blank=True)
    delivery_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    delivery_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    # Passport upload
    passport_image = models.FileField(upload_to='buyer_passports/', blank=True, null=True)
    
    order_message_template = models.TextField(blank=True, default='')
    quick_replies = models.TextField(blank=True, default='')

    def __str__(self):
        return f"BuyerProfile({self.user.username})"


class KYCSelfie(models.Model):
    """Stores the 5 liveness-check selfies captured during registration."""

    STATUS_CHOICES = [
        ('pending',  'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user           = models.OneToOneField(User, on_delete=models.CASCADE, related_name='kyc_selfie')
    selfie_center  = models.ImageField(upload_to='kyc_selfies/', blank=True, null=True)
    selfie_left    = models.ImageField(upload_to='kyc_selfies/', blank=True, null=True)
    selfie_right   = models.ImageField(upload_to='kyc_selfies/', blank=True, null=True)
    selfie_up      = models.ImageField(upload_to='kyc_selfies/', blank=True, null=True)
    selfie_down    = models.ImageField(upload_to='kyc_selfies/', blank=True, null=True)
    status         = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    admin_notes    = models.TextField(blank=True, null=True)
    submitted_at   = models.DateTimeField(auto_now_add=True)
    reviewed_at    = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"KYC({self.user.username}) — {self.status}"
