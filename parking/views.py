from rest_framework import viewsets, permissions, views
from rest_framework.response import Response
from django.db.models import Sum
from .models import ParkingSpace, Booking, Payment, ParkingLot
from .serializers import ParkingSpaceSerializer, BookingSerializer, PaymentSerializer, ParkingLotSerializer

class CustomerStatsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        bookings = Booking.objects.filter(user=user)
        total_bookings = bookings.count()
        active_bookings = bookings.filter(status='active').count()
        total_spent = Payment.objects.filter(booking__user=user, is_paid=True).aggregate(total=Sum('amount'))['total'] or 0
        
        # Simple loyalty logic
        loyalty = "Member"
        if total_bookings >= 10:
            loyalty = "VIP"
        elif total_bookings >= 5:
            loyalty = "Loyal"

        return Response({
            'total_bookings': total_bookings,
            'active_bookings': active_bookings,
            'total_spent': float(total_spent),
            'loyalty_level': loyalty
        })

class ParkingLotViewSet(viewsets.ModelViewSet):
# ... existing code ...
    queryset = ParkingLot.objects.all()
    serializer_class = ParkingLotSerializer
    permission_classes = [permissions.AllowAny]

class ParkingSpaceViewSet(viewsets.ModelViewSet):
    queryset = ParkingSpace.objects.all()
    serializer_class = ParkingSpaceSerializer
    permission_classes = [permissions.AllowAny]

class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Booking.objects.all().order_by('-created_at')
        return Booking.objects.filter(user=user).order_by('-created_at')

    def perform_create(self, serializer):
        from .models import Payment
        from django.utils.dateparse import parse_datetime
        import math
        
        booking = serializer.save()
        
        # Update space status to booked
        booking.space.status = 'booked'
        booking.space.save()
        
        # Calculate duration and payment amount
        if booking.end_time and booking.start_time:
            duration = booking.end_time - booking.start_time
            hours = math.ceil(duration.total_seconds() / 3600)
            if hours < 1:
                hours = 1
            amount = hours * booking.space.price_per_hour
        else:
            amount = booking.space.price_per_hour

        # Generate a pending payment for this booking
        Payment.objects.create(
            booking=booking,
            amount=amount,
            is_paid=True
        )
class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            # Admin sees all payments, newest first
            return Payment.objects.all().order_by('-timestamp')
        # Regular customer sees only their own payments
        return Payment.objects.filter(booking__user=user).order_by('-timestamp')
