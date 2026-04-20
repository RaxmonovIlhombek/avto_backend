from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Booking, Payment, Notification

@receiver(post_save, sender=Booking)
def create_booking_notification(sender, instance, created, **kwargs):
    if created:
        # Foydalanuvchi uchun xabarnoma
        Notification.objects.create(
            user=instance.user,
            title="Yangi bron yaratildi",
            message=f"Sizning {instance.space.identifier} sektori uchun broningiz tasdiqlandi. QR-tokendan foydalanishingiz mumkin.",
            notification_type='booking'
        )
        
        # Admin uchun xabarnoma
        admins = User.objects.filter(is_staff=True)
        for admin in admins:
            Notification.objects.create(
                user=admin,
                title="Yangi bron tushdi",
                message=f"Foydalanuvchi {instance.user.username} {instance.space.identifier} sektorini bron qildi.",
                notification_type='booking'
            )

@receiver(post_save, sender=Payment)
def create_payment_notification(sender, instance, created, **kwargs):
    if instance.is_paid:
        # Foydalanuvchi uchun xabarnoma
        Notification.objects.create(
            user=instance.booking.user,
            title="To'lov muvaffaqiyatli",
            message=f"Parking uchun {instance.amount} so'm miqdoridagi to'lovingiz qabul qilindi.",
            notification_type='payment'
        )
        
        # Admin uchun xabarnoma
        admins = User.objects.filter(is_staff=True)
        for admin in admins:
            Notification.objects.create(
                user=admin,
                title="Yangi to'lov",
                message=f"{instance.booking.user.username} tomonidan {instance.amount} so'm to'landi.",
                notification_type='payment'
            )
