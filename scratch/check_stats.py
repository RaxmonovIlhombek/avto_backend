import os
import django
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
# Add current directory to path so 'core' can be found
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')
django.setup()

from parking.models import Payment
from django.db.models import Sum
from datetime import timedelta
from django.utils import timezone

def check_stats():
    today = timezone.now().date()
    month_start = today.replace(day=1)
    
    total_revenue = Payment.objects.filter(is_paid=True).aggregate(total=Sum('amount'))['total'] or 0
    month_revenue = Payment.objects.filter(is_paid=True, timestamp__date__gte=month_start).aggregate(total=Sum('amount'))['total'] or 0
    
    print(f"Total Revenue: {total_revenue}")
    print(f"Monthly Revenue: {month_revenue}")

if __name__ == "__main__":
    check_stats()
