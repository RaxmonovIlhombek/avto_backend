from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    car_number = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return f"Profile for {self.user.username}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

class ParkingLot(models.Model):
    name = models.CharField(max_length=100, help_text="e.g., Yunusobod filiali")
    address = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    image = models.ImageField(upload_to='parking_lots/', null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    contact_phone = models.CharField(max_length=50, null=True, blank=True)
    contact_email = models.EmailField(null=True, blank=True)
    working_hours = models.CharField(max_length=100, null=True, blank=True, help_text="e.g., 24/7 or 09:00-21:00")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ParkingSpace(models.Model):
    SPACE_TYPES = [
        ('regular', 'Regular'),
        ('vip', 'VIP'),
        ('disabled', 'Disabled'),
    ]
    
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('booked', 'Booked'),
        ('maintenance', 'Maintenance'),
    ]

    parking_lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE, related_name='spaces', null=True, blank=True)
    identifier = models.CharField(max_length=10, unique=True, help_text="e.g., A1, B2")
    space_type = models.CharField(max_length=20, choices=SPACE_TYPES, default='regular')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2, default=5000.00)
    
    def __str__(self):
        return f"{self.identifier} ({self.space_type}) - {self.parking_lot.name if self.parking_lot else 'No Lot'}"

class Booking(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    space = models.ForeignKey(ParkingSpace, on_delete=models.CASCADE, related_name='bookings')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Yangi maydonlar
    car_number = models.CharField(max_length=20, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    qr_token = models.CharField(max_length=100, unique=True, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.qr_token:
            self.qr_token = str(uuid.uuid4())
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Booking {self.id} - {self.car_number} ({self.space.identifier})"

class Payment(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Payment of {self.amount} for booking {self.booking.id}"
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('booking', 'Booking'),
        ('payment', 'Payment'),
        ('system', 'System'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='system')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.user.username}"
