import random
import uuid
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from parking.models import ParkingLot, ParkingSpace, Booking, Payment, Notification

class Command(BaseCommand):
    help = 'Seeds the database with realistic sample data'

    def handle(self, *args, **options):
        self.stdout.write('Seeding data...')

        # 1. Create/Ensure an Admin user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@smartpark.uz',
                'is_staff': True,
                'is_superuser': True,
                'first_name': 'Admin',
                'last_name': 'SmartPark'
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write('Created admin user: admin / admin123')

        # 2. Create Parking Lots
        lots_data = [
            {
                'name': 'Tashkent City Center',
                'address': 'Amir Temur shoh ko\'chasi, Toshkent',
                'description': 'Shaharning qoq markazida joylashgan eng zamonaviy avtoturargoh.',
                'working_hours': '24/7'
            },
            {
                'name': 'Chorsu Market Plaza',
                'address': 'Beruniy ko\'chasi, Chorsu, Toshkent',
                'description': 'Tarixiy bozor yaqinidagi qulay va xavfsiz joy.',
                'working_hours': '06:00 - 22:00'
            },
            {
                'name': 'Yunusobod Business Hub',
                'address': 'Amir Temur ko\'chasi, Yunusobod',
                'description': 'Biznes markazlar va ofislar uchun mo\'ljallangan premium turargoh.',
                'working_hours': '24/7'
            },
            {
                'name': 'Airport Terminal 2',
                'address': 'Qumariq ko\'chasi, Toshkent Aeroporti',
                'description': 'Xalqaro aeroport yaqinidagi uzoq muddatli turargoh.',
                'working_hours': '24/7'
            }
        ]

        lots = []
        for data in lots_data:
            lot, _ = ParkingLot.objects.get_or_create(name=data['name'], defaults=data)
            lots.append(lot)

        # 3. Create Parking Spaces
        space_types = ['regular', 'vip', 'disabled']
        space_statuses = ['available', 'occupied', 'booked', 'maintenance']
        
        identifiers = []
        for char in 'ABCDE':
            for i in range(1, 21):
                identifiers.append(f"{char}{i}")

        spaces = []
        for i, identifier in enumerate(identifiers):
            # To avoid unique constraint errors if some exist
            if ParkingSpace.objects.filter(identifier=identifier).exists():
                continue
                
            lot = random.choice(lots)
            s_type = random.choices(space_types, weights=[70, 20, 10])[0]
            status = random.choices(space_statuses, weights=[60, 20, 15, 5])[0]
            price = 5000 if s_type == 'regular' else 15000 if s_type == 'vip' else 4000
            
            space = ParkingSpace.objects.create(
                parking_lot=lot,
                identifier=identifier,
                space_type=s_type,
                status=status,
                price_per_hour=price
            )
            spaces.append(space)

        # 4. Create dummy regular users
        users = []
        user_names = [
            ('ilmkhon', 'Ilhomxon', 'Raxmonov'),
            ('bekzod', 'Bekzod', 'Alimov'),
            ('aziz_dev', 'Azizbek', 'Karimov'),
            ('nodira', 'Nodira', 'Saidova'),
            ('jasur_77', 'Jasur', 'Xolmatov')
        ]

        for uname, fname, lname in user_names:
            u, created = User.objects.get_or_create(
                username=uname,
                defaults={
                    'email': f'{uname}@gmail.com',
                    'first_name': fname,
                    'last_name': lname
                }
            )
            if created:
                u.set_password('pass123')
                u.save()
            users.append(u)

        # 5. Create historical and active bookings
        now = timezone.now()
        car_prefixes = ['01', '10', '20', '40', '90']
        car_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']

        for i in range(50):
            user = random.choice(users)
            space = random.choice(spaces)
            
            # Determine booking status
            # Some completed, some active
            if i < 40: # Historical
                status = 'completed'
                start = now - timedelta(days=random.randint(1, 30), hours=random.randint(0, 23))
                end = start + timedelta(hours=random.randint(1, 10))
            else: # Active
                status = 'active'
                start = now - timedelta(hours=random.randint(0, 5))
                end = start + timedelta(hours=random.randint(1, 5))
                space.status = 'occupied' if i % 2 == 0 else 'booked'
                space.save()

            car_num = f"{random.choice(car_prefixes)} {random.randint(100, 999)} {random.choice(car_letters)}{random.choice(car_letters)}"
            
            booking = Booking.objects.create(
                user=user,
                space=space,
                start_time=start,
                end_time=end,
                status=status,
                car_number=car_num,
                phone_number=f'+998 9{random.randint(0, 9)} {random.randint(100, 999)} {random.randint(10, 99)} {random.randint(10, 99)}'
            )

            # Create payment for each booking
            hours = max(1, int((end - start).total_seconds() / 3600)) if end else 1
            amount = hours * space.price_per_hour
            
            Payment.objects.create(
                booking=booking,
                amount=amount,
                is_paid=True if status == 'completed' else random.choice([True, False]),
                transaction_id=str(uuid.uuid4())[:18].upper()
            )

            # Create some notifications
            if i % 3 == 0:
                Notification.objects.create(
                    user=user,
                    title="Bron tasdiqlandi" if status == 'active' else "To'lov muvaffaqiyatli",
                    message=f"Sizning {space.identifier} joy uchun broningiz holati: {status}.",
                    notification_type='booking',
                    is_read=random.choice([True, False])
                )

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {len(lots)} lots, {len(spaces)} spaces, and 50 bookings.'))
