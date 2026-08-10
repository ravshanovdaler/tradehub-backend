from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from orders.models import Order
from chat.models import ChatMessage
from accounts.models import SellerProfile, KYCSelfie, Report
from .utils import send_notification_to_user

User = get_user_model()

# --- Order Signals ---

@receiver(pre_save, sender=Order)
def order_pre_save(sender, instance, **kwargs):
    if instance.id:
        try:
            original = Order.objects.get(id=instance.id)
            instance._original_status = original.status
        except Order.DoesNotExist:
            instance._original_status = None
    else:
        instance._original_status = None

@receiver(post_save, sender=Order)
def order_post_save(sender, instance, created, **kwargs):
    if created:
        # New Sale notification to Seller
        text = (
            f"🔔 *New Sale!*\n"
            f"Order #`{instance.id}` has been placed by *{instance.buyer.username}*.\n"
            f"💰 *Total Price:* {instance.total_price} {instance.currency}\n"
            f"📊 *Status:* {instance.get_status_display()}"
        )
        send_notification_to_user(instance.seller, text)
    else:
        # Update notification if status changed
        original_status = getattr(instance, '_original_status', None)
        if original_status and original_status != instance.status:
            text = (
                f"📦 *Order Status Updated*\n"
                f"Order #`{instance.id}` has been updated to *{instance.get_status_display()}*."
            )
            # Notify both buyer and seller of the change
            send_notification_to_user(instance.buyer, text)
            send_notification_to_user(instance.seller, text)


# --- Chat Message Signals ---

@receiver(post_save, sender=ChatMessage)
def chat_message_post_save(sender, instance, created, **kwargs):
    if created:
        room = instance.room
        # Identify the recipient
        if instance.sender == room.buyer:
            recipient = room.seller
        else:
            recipient = room.buyer

        text = (
            f"💬 *New Message from {instance.sender.username}*\n\n"
            f"{instance.message or '(Media/Attachment)'}"
        )
        send_notification_to_user(recipient, text)


# --- Seller Profile (Verification) Signals ---

@receiver(pre_save, sender=SellerProfile)
def seller_profile_pre_save(sender, instance, **kwargs):
    if instance.id:
        try:
            original = SellerProfile.objects.get(id=instance.id)
            instance._original_verified = original.is_verified
        except SellerProfile.DoesNotExist:
            instance._original_verified = False
    else:
        instance._original_verified = False

@receiver(post_save, sender=SellerProfile)
def seller_profile_post_save(sender, instance, created, **kwargs):
    original_verified = getattr(instance, '_original_verified', False)
    if not original_verified and instance.is_verified:
        text = (
            f"✅ *Seller Profile Verified!*\n"
            f"Your seller account for *{instance.company_name}* has been verified by the administration. "
            f"You can now list products and start selling!"
        )
        send_notification_to_user(instance.user, text)


# --- KYC Selfie Signals ---

@receiver(pre_save, sender=KYCSelfie)
def kyc_selfie_pre_save(sender, instance, **kwargs):
    if instance.id:
        try:
            original = KYCSelfie.objects.get(id=instance.id)
            instance._original_status = original.status
        except KYCSelfie.DoesNotExist:
            instance._original_status = None
    else:
        instance._original_status = None

@receiver(post_save, sender=KYCSelfie)
def kyc_selfie_post_save(sender, instance, created, **kwargs):
    original_status = getattr(instance, '_original_status', None)
    if original_status and original_status != instance.status:
        text = (
            f"👤 *KYC Verification Update*\n"
            f"Your KYC Selfie verification status has been updated to: *{instance.get_status_display()}*.\n"
            f"📝 *Notes:* {instance.admin_notes or 'No notes provided.'}"
        )
        send_notification_to_user(instance.user, text)


# --- Report Signals ---

@receiver(post_save, sender=Report)
def report_post_save(sender, instance, created, **kwargs):
    if created:
        text = (
            f"⚠️ *New Report Submitted*\n"
            f"• *Reporter:* {instance.reporter.username}\n"
            f"• *Type:* {instance.get_report_type_display()}\n"
            f"• *Reason:* {instance.reason}\n"
            f"• *Description:* {instance.description}"
        )
        staff_users = User.objects.filter(is_staff=True)
        for staff in staff_users:
            send_notification_to_user(staff, text)
