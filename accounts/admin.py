from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils import timezone
from .models import SellerProfile, BuyerProfile, SellerDeletionRequest, CompanyLike, KYCSelfie


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
    list_display = ('company_name', 'user', 'registration_number', 'is_verified', 'has_passport', 'has_business_doc')
    list_filter = ('is_verified',)
    search_fields = ('company_name', 'registration_number', 'user__username')
    readonly_fields = ('passport_preview', 'business_doc_link')
    actions = ['approve_sellers', 'reject_sellers']

    def has_passport(self, obj):
        return bool(obj.passport_image)
    has_passport.boolean = True
    has_passport.short_description = 'Passport'

    def has_business_doc(self, obj):
        return bool(obj.business_doc)
    has_business_doc.boolean = True
    has_business_doc.short_description = 'Business Doc'

    def passport_preview(self, obj):
        if obj.passport_image:
            return format_html('<img src="{}" style="max-width:300px;max-height:200px;border-radius:6px"/>', obj.passport_image.url)
        return '-'
    passport_preview.short_description = 'Passport Preview'

    def business_doc_link(self, obj):
        if obj.business_doc:
            return format_html('<a href="{}" target="_blank">Download Business Doc</a>', obj.business_doc.url)
        return '-'
    business_doc_link.short_description = 'Business Document'

    def approve_sellers(self, request, queryset):
        queryset.update(is_verified=True)
    approve_sellers.short_description = "Approve selected manufacturers"

    def reject_sellers(self, request, queryset):
        queryset.update(is_verified=False)
    reject_sellers.short_description = "Reject/Suspend selected manufacturers"


class BuyerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'delivery_address', 'has_passport')
    search_fields = ('user__username', 'delivery_address')
    readonly_fields = ('passport_preview',)

    def has_passport(self, obj):
        return bool(obj.passport_image)
    has_passport.boolean = True
    has_passport.short_description = 'Passport'

    def passport_preview(self, obj):
        if obj.passport_image:
            return format_html('<img src="{}" style="max-width:300px;max-height:200px;border-radius:6px"/>', obj.passport_image.url)
        return '-'
    passport_preview.short_description = 'Passport Preview'


@admin.register(KYCSelfie)
class KYCSelfieAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'selfie_count', 'submitted_at', 'reviewed_at')
    list_filter = ('status',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = (
        'user', 'submitted_at', 'reviewed_at',
        'selfie_center_preview', 'selfie_left_preview',
        'selfie_right_preview', 'selfie_up_preview', 'selfie_down_preview',
    )
    fieldsets = (
        ('User', {'fields': ('user', 'submitted_at', 'reviewed_at')}),
        ('Admin Review', {'fields': ('status', 'admin_notes')}),
        ('Face Scan Selfies', {
            'fields': (
                'selfie_center_preview', 'selfie_left_preview',
                'selfie_right_preview', 'selfie_up_preview', 'selfie_down_preview',
            )
        }),
    )
    actions = ['approve_kyc', 'reject_kyc']

    def selfie_count(self, obj):
        count = sum([
            bool(obj.selfie_center), bool(obj.selfie_left), bool(obj.selfie_right),
            bool(obj.selfie_up), bool(obj.selfie_down),
        ])
        color = '#10B981' if count == 5 else '#F59E0B' if count > 0 else '#EF4444'
        return format_html('<b style="color:{}">{}/5 poses</b>', color, count)
    selfie_count.short_description = 'Selfies'

    def _selfie_preview(self, field_obj, label):
        if field_obj:
            return format_html(
                '<div style="display:inline-block;text-align:center;margin:4px">'
                '<img src="{}" style="max-width:180px;max-height:240px;border-radius:8px;border:2px solid #374151"/>'
                '<br><small>{}</small></div>',
                field_obj.url, label
            )
        return format_html('<span style="color:#888">Not provided</span>')

    def selfie_center_preview(self, obj):
        return self._selfie_preview(obj.selfie_center, 'Straight (Center)')
    def selfie_left_preview(self, obj):
        return self._selfie_preview(obj.selfie_left, 'Left')
    def selfie_right_preview(self, obj):
        return self._selfie_preview(obj.selfie_right, 'Right')
    def selfie_up_preview(self, obj):
        return self._selfie_preview(obj.selfie_up, 'Up')
    def selfie_down_preview(self, obj):
        return self._selfie_preview(obj.selfie_down, 'Down')

    selfie_center_preview.short_description = 'Center Selfie'
    selfie_left_preview.short_description   = 'Left Selfie'
    selfie_right_preview.short_description  = 'Right Selfie'
    selfie_up_preview.short_description     = 'Up Selfie'
    selfie_down_preview.short_description   = 'Down Selfie'

    def approve_kyc(self, request, queryset):
        updated = queryset.update(status='approved', reviewed_at=timezone.now())
        self.message_user(request, f'Approved KYC for {updated} user(s).')
    approve_kyc.short_description = 'Approve selected KYC submissions'

    def reject_kyc(self, request, queryset):
        updated = queryset.update(status='rejected', reviewed_at=timezone.now())
        self.message_user(request, f'Rejected KYC for {updated} user(s).')
    reject_kyc.short_description = 'Reject selected KYC submissions'

    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)


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




