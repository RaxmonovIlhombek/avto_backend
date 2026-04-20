import os
import django

# Set up Django environment
import sys
# Add current directory to path so 'core' can be found
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from parking.models import Payment

def fix_payments():
    # Find all payments that are currently unpaid
    unpaid_payments = Payment.objects.filter(is_paid=False)
    count = unpaid_payments.count()
    
    if count == 0:
        print("No unpaid payments found. Statistics should be correct.")
        return

    print(f"Found {count} unpaid payments. Updating to 'paid'...")
    
    # Update all to is_paid=True
    # We use a loop to trigger signals (though signals.py only triggers on creation or if is_paid becomes true)
    # Actually, signals.py triggers on post_save if instance.is_paid is true.
    for payment in unpaid_payments:
        payment.is_paid = True
        payment.save()
        
    print(f"Successfully updated {count} payments. Monthly income statistics should now be updated.")

if __name__ == "__main__":
    fix_payments()
