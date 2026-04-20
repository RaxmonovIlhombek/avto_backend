import os
import django
import random
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from parking.models import ParkingSpace, Booking, Payment

def populate():
    print("Dummy ma'lumotlar yaratish boshlandi...")
    
    # 1. Admin va Test User
    admin, _ = User.objects.get_or_create(username='admin')
    admin.set_password('admin123')
    admin.is_staff = True
    admin.is_superuser = True
    admin.save()

    testuser, _ = User.objects.get_or_create(username='testuser')
    testuser.set_password('pass123')
    testuser.save()

    # 2. Parking Spaces
    ParkingSpace.objects.all().delete()
    spaces = []
    # Regular spaces
    for i in range(1, 11):
        spaces.append(ParkingSpace(identifier=f'A{i}', space_type='regular', price_per_hour=5000))
    # VIP spaces
    for i in range(1, 6):
        spaces.append(ParkingSpace(identifier=f'V{i}', space_type='vip', price_per_hour=15000))
    
    ParkingSpace.objects.bulk_create(spaces)
    all_spaces = list(ParkingSpace.objects.all())

    # 3. Chart uchun so'nggi 7 kunlik Bookings va Payments
    print("Grafik uchun tarixiy ma'lumotlar yaratilmoqda...")
    Booking.objects.all().delete()
    Payment.objects.all().delete()

    for i in range(7, -1, -1):
        date = timezone.now() - timedelta(days=i)
        # Har bir kun uchun 3-8 ta bron yaratamiz
        for _ in range(random.randint(3, 8)):
            space = random.choice(all_spaces)
            start_time = date.replace(hour=random.randint(8, 20), minute=0)
            end_time = start_time + timedelta(hours=random.randint(1, 4))
            
            car_number = f"{random.randint(1, 99):02} {random.choice('ABCDEFGH')} {random.randint(100, 999)} {random.choice('AB')}{random.choice('AB')}"
            phone_number = f"+998 (90) {random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10, 99)}"
            
            booking = Booking.objects.create(
                user=testuser,
                space=space,
                start_time=start_time,
                end_time=end_time,
                status='completed',
                car_number=car_number,
                phone_number=phone_number
            )
            # Tarixiy ma'lumotlar created_at ni o'zgartira olmaymiz (auto_now_add=True)
            # lekin biz view_admin.py ni timestamp__date bo'yicha filterladik.
            # Shuning uchun Payment.timestamp orqali boshqaramiz
            
            payment = Payment.objects.create(
                booking=booking,
                amount=space.price_per_hour * (random.randint(1, 3)),
                is_paid=True,
                transaction_id=f"TXN-{random.randint(10000, 99999)}"
            )
            # Payment timestampni o'tmishga o'tkazamiz
            Payment.objects.filter(id=payment.id).update(timestamp=start_time)

    print("Tayyor! Endi dashboardda chiroyli grafiklar ko'rinadi.")

if __name__ == '__main__':
    populate()
