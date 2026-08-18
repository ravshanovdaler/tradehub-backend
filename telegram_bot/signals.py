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
        send_notification_to_user(
            instance.seller,
            'notif_new_sale',
            order_id=instance.id,
            buyer=instance.buyer.username,
            total_price=instance.total_price,
            currency=instance.currency,
            status=instance.get_status_display()
        )
    else:
        # Update notification if status changed
        original_status = getattr(instance, '_original_status', None)
        if original_status and original_status != instance.status:
            # Notify both buyer and seller of the change
            send_notification_to_user(
                instance.buyer,
                'notif_order_status_updated',
                order_id=instance.id,
                status=instance.get_status_display()
            )
            send_notification_to_user(
                instance.seller,
                'notif_order_status_updated',
                order_id=instance.id,
                status=instance.get_status_display()
            )


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

        send_notification_to_user(
            recipient,
            'notif_new_chat_message',
            sender=instance.sender.username,
            message=instance.message or '(Media/Attachment)'
        )


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
        send_notification_to_user(
            instance.user,
            'notif_seller_verified',
            company_name=instance.company_name
        )


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
        send_notification_to_user(
            instance.user,
            'notif_kyc_updated',
            status=instance.get_status_display(),
            notes=instance.admin_notes or 'No notes provided.'
        )


# --- Report Signals ---

@receiver(post_save, sender=Report)
def report_post_save(sender, instance, created, **kwargs):
    if created:
        staff_users = User.objects.filter(is_staff=True)
        for staff in staff_users:
            send_notification_to_user(
                staff,
                'notif_report_submitted',
                reporter=instance.reporter.username,
                type=instance.get_report_type_display(),
                reason=instance.reason,
                description=instance.description
            )
