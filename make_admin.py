import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User

def make_admin():
    u, created = User.objects.get_or_create(username='admin', defaults={'email': 'admin@park.uz'})
    u.set_password('admin123')
    u.is_staff = True
    u.is_superuser = True
    u.save()
    
    # testuser ni ham staff qilish (agar mavjud bo'lsa)
    test_u = User.objects.filter(username='testuser').first()
    if test_u:
        test_u.is_staff = True
        test_u.save()
        
    print("Admin foydalanuvchilar tayyor:")
    print("1. Login: admin, Parol: admin123")
    print("2. Login: testuser, Parol: pass123 (Menejer huquqi bilan)")

if __name__ == '__main__':
    make_admin()
