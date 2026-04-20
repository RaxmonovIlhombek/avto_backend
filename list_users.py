import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

print("=== FOYDALANUVCHILAR ===")
for u in User.objects.all():
    try:
        token = Token.objects.get(user=u)
        token_str = token.key[:10] + "..."
    except Token.DoesNotExist:
        token_str = "TOKEN YO'Q"
    print(f"ID:{u.id} | {u.username} | staff:{u.is_staff} | active:{u.is_active} | token:{token_str}")

print(f"\nJami: {User.objects.count()} ta foydalanuvchi")
