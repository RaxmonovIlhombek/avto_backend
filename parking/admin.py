from django.contrib import admin
from .models import ParkingSpace, Booking, Payment

@admin.register(ParkingSpace)
class ParkingSpaceAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'space_type', 'status', 'price_per_hour')
    list_filter = ('space_type', 'status')
    search_fields = ('identifier',)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'space', 'start_time', 'end_time', 'status')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'space__identifier')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'amount', 'timestamp', 'is_paid')
    list_filter = ('is_paid', 'timestamp')
