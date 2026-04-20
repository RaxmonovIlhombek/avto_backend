import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from parking.models import Booking, Payment
import math

bookings = Booking.objects.all()
created = 0
updated = 0

for booking in bookings:
    if not hasattr(booking, 'payment'):
        if booking.end_time and booking.start_time:
            duration = booking.end_time - booking.start_time
            hours = math.ceil(duration.total_seconds() / 3600)
            if hours < 1:
                hours = 1
            amount = hours * booking.space.price_per_hour
        else:
            amount = booking.space.price_per_hour
            
        Payment.objects.create(
            booking=booking,
            amount=amount,
            is_paid=True
        )
        created += 1
    else:
        # Just ensure they are paid so the user sees the yield changing in UI
        if not booking.payment.is_paid:
            booking.payment.is_paid = True
            booking.payment.save()
            updated += 1
            
print(f"Retroactively created {created} payments and updated {updated} payments to is_paid=True.")
