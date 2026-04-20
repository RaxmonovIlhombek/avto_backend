import os
import django
import time
from datetime import datetime, timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from parking.models import Booking, ParkingSpace

def cleanup_bookings():
    print("Starting booking cleanup task...")
    while True:
        try:
            # 5 minutes buffer
            buffer_time = timezone.now() - timedelta(minutes=5)
            
            # Find active bookings that have ended more than 5 minutes ago
            expired_bookings = Booking.objects.filter(
                status='active',
                end_time__lte=buffer_time
            )
            
            if expired_bookings.exists():
                print(f"Found {expired_bookings.count()} expired bookings.")
                for booking in expired_bookings:
                    # Set space back to available
                    space = booking.space
                    space.status = 'available'
                    space.save()
                    
                    # Mark booking as completed
                    booking.status = 'completed'
                    booking.save()
                    print(f"Space {space.identifier} is now available.")
            
        except Exception as e:
            print(f"Error in cleanup: {e}")
            
        time.sleep(60) # Check every minute

if __name__ == "__main__":
    cleanup_bookings()
