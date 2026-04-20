from rest_framework import serializers
from .models import ParkingSpace, Booking, Payment, Profile, ParkingLot, Notification
from django.contrib.auth.models import User

# ... existing code ...

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['phone_number', 'car_number']

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    booking_count = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_staff', 'is_active', 'profile', 'booking_count', 'total_spent']

    def get_booking_count(self, obj):
        # Return annotated value if present, else calculate
        return getattr(obj, 'booking_count', obj.bookings.count())

    def get_total_spent(self, obj):
        # Return annotated value if present, else calculate
        from django.db.models import Sum
        if hasattr(obj, 'total_spent'):
            return obj.total_spent or 0
        return obj.bookings.filter(payment__is_paid=True).aggregate(total=Sum('payment__amount'))['total'] or 0

class ParkingLotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingLot
        fields = '__all__'

class ParkingSpaceSerializer(serializers.ModelSerializer):
    parking_lot_detail = ParkingLotSerializer(source='parking_lot', read_only=True)
    
    class Meta:
        model = ParkingSpace
        fields = '__all__'

class BookingSerializer(serializers.ModelSerializer):
    user_detail = UserSerializer(source='user', read_only=True)
    space_detail = ParkingSpaceSerializer(source='space', read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'user', 'space', 'start_time', 'end_time', 
            'status', 'created_at', 'user_detail', 'space_detail',
            'car_number', 'phone_number', 'qr_token'
        ]
        read_only_fields = ['qr_token']

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user
