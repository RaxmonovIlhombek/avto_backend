import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User

try:
    user = User.objects.filter(username='admin').first()
    if user:
        user.is_staff = True
        user.is_superuser = True
        user.save()
        print(f"Successfully verified/fixed admin: {user.username}")
    else:
        print("Admin user not found")
except Exception as e:
    print(f"Error: {e}")
