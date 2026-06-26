from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import SellerProfile, BuyerProfile, SellerDeletionRequest, CompanyLike


User = get_user_model()


class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'is_seller', 'is_buyer', 'email_verified', 'is_staff')
    list_filter = ('is_seller', 'is_buyer', 'email_verified', 'is_staff', 'is_superuser')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Roles', {'fields': ('is_seller', 'is_buyer')}),
        ('Contact Info', {'fields': ('phone_number', 'additional_phone', 'age')}),
        ('Email Verification', {'fields': ('email_verified', 'email_otp')}),
        ('Deletion Request', {'fields': ('deletion_requested', 'deletion_requested_at')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Roles', {'fields': ('is_seller', 'is_buyer')}),
        ('Contact Info', {'fields': ('phone_number', 'additional_phone', 'age')}),
    )


class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'user', 'registration_number', 'business_address', 'is_verified')
    list_filter = ('is_verified',)
    search_fields = ('company_name', 'registration_number', 'user__username')
    actions = ['approve_sellers', 'reject_sellers']

    def approve_sellers(self, request, queryset):
        queryset.update(is_verified=True)
    approve_sellers.short_description = "Approve selected manufacturers"

    def reject_sellers(self, request, queryset):
        queryset.update(is_verified=False)
    reject_sellers.short_description = "Reject/Suspend selected manufacturers"


class BuyerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'delivery_address')
    search_fields = ('user__username', 'delivery_address')


class SellerDeletionRequestAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'phone_number', 'deletion_requested_at')
    search_fields = ('username', 'email')
    actions = ['approve_deletion', 'recover_account']

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_seller=True, deletion_requested=True)

    def approve_deletion(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"Permanently deleted {count} seller account(s).")
    approve_deletion.short_description = "Approve Deletion (Permanently Purge)"

    def recover_account(self, request, queryset):
        count = queryset.update(deletion_requested=False, deletion_requested_at=None)
        self.message_user(request, f"Recovered {count} seller account(s).")
    recover_account.short_description = "Recover Account (Clear Deletion Request)"


admin.site.register(User, UserAdmin)
admin.site.register(SellerProfile, SellerProfileAdmin)
admin.site.register(BuyerProfile, BuyerProfileAdmin)
admin.site.register(SellerDeletionRequest, SellerDeletionRequestAdmin)
admin.site.register(CompanyLike)


