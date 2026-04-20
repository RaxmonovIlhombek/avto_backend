from rest_framework import views, permissions, status
from rest_framework.response import Response
from django.db.models import Sum, Count, Q, Avg
from django.db.models.functions import TruncDate, ExtractHour, ExtractWeekDay
from .models import ParkingSpace, Booking, Payment, ParkingLot, Profile
from .serializers import BookingSerializer, UserSerializer
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from django.http import HttpResponse
import openpyxl
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

class AdminStatsView(views.APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        today = timezone.now().date()
        seven_days_ago = today - timedelta(days=7)

        total_revenue = Payment.objects.filter(is_paid=True).aggregate(total=Sum('amount'))['total'] or 0
        total_bookings = Booking.objects.count()
        total_spaces = ParkingSpace.objects.count()
        total_lots = ParkingLot.objects.count()
        occupied_spaces = ParkingSpace.objects.filter(status__in=['occupied', 'booked']).count()
        
        # Bandlik foizi
        occupancy_rate = (occupied_spaces / total_spaces * 100) if total_spaces > 0 else 0
        
        # Chart uchun kunlik tushum (Granular ma'lumotlar bilan)
        daily_revenue = Payment.objects.filter(
            timestamp__date__gte=seven_days_ago
        ).annotate(date=TruncDate('timestamp')).values('date').annotate(
            paid_amount=Sum('amount', filter=Q(is_paid=True)),
            pending_amount=Sum('amount', filter=Q(is_paid=False)),
            total_amount=Sum('amount'),
            count=Count('id')
        ).order_by('date')
        
        chart_data = []
        for i in range(7):
            date = seven_days_ago + timedelta(days=i)
            day_data = next((item for item in daily_revenue if item['date'] == date), None)
            chart_data.append({
                'name': date.strftime('%d-%b'),
                'revenue': float(day_data['paid_amount'] or 0) if day_data else 0,
                'pending_revenue': float(day_data['pending_amount'] or 0) if day_data else 0,
                'all_revenue': float(day_data['total_amount'] or 0) if day_data else 0,
                'bookings': day_data['count'] if day_data else 0
            })

        # --- YANGI BI ANALITIKA ---
        # Soatlar bo'yicha faollik (0-23)
        hourly_data = Booking.objects.annotate(hour=ExtractHour('start_time')).values('hour').annotate(count=Count('id')).order_by('hour')
        hourly_trends = [{'hour': h, 'count': 0} for h in range(24)]
        for item in hourly_data:
            hourly_trends[item['hour']]['count'] = item['count']

        # Haftaning kunlari bo'yicha faollik
        # ExtractWeekDay: 1 (Sunday) to 7 (Saturday)
        daily_vol_data = Booking.objects.annotate(weekday=ExtractWeekDay('start_time')).values('weekday').annotate(count=Count('id')).order_by('weekday')
        weekday_map = {1: 'Sun', 2: 'Mon', 3: 'Tue', 4: 'Wed', 5: 'Thu', 6: 'Fri', 7: 'Sat'}
        daily_trends = [{'name': weekday_map[i], 'count': 0} for i in range(1, 8)]
        for item in daily_vol_data:
            # item['weekday'] can sometimes be slightly different depending on DB, but standard is 1-7
            idx = item['weekday'] - 1
            if 0 <= idx < 7:
                daily_trends[idx]['count'] = item['count']

        # O'rtacha tushum
        avg_payment = Payment.objects.filter(is_paid=True).aggregate(avg=Avg('amount'))['avg'] or 0

        # Bugungi tushum
        today_revenue = Payment.objects.filter(is_paid=True, timestamp__date=today).aggregate(total=Sum('amount'))['total'] or 0
        
        # Shu oydagi tushum
        month_start = today.replace(day=1)
        month_revenue = Payment.objects.filter(is_paid=True, timestamp__date__gte=month_start).aggregate(total=Sum('amount'))['total'] or 0
        # ---------------------------

        recent_bookings = Booking.objects.all().order_by('-created_at')[:10]
        serializer = BookingSerializer(recent_bookings, many=True)
        
        # Sector bo'yicha daromad
        revenue_by_sector = Booking.objects.filter(status='completed').values('space__identifier').annotate(total=Sum('payment__amount')).order_by('-total')[:5]

        # Filiallar bo'yicha daromad
        revenue_by_lot = ParkingLot.objects.annotate(
            total_revenue=Sum('spaces__bookings__payment__amount', filter=Q(spaces__bookings__payment__is_paid=True))
        ).values('name', 'total_revenue')

        # Filiallar bo'yicha bandlik
        lots_occupancy = []
        for lot in ParkingLot.objects.all():
            spaces = lot.spaces.all()
            total = spaces.count()
            occupied = spaces.filter(status__in=['occupied', 'booked']).count()
            lots_occupancy.append({
                'name': lot.name,
                'total': total,
                'occupied': occupied,
                'rate': round((occupied / total * 100), 1) if total > 0 else 0
            })

        return Response({
            'total_revenue': float(total_revenue),
            'today_revenue': float(today_revenue),
            'month_revenue': float(month_revenue),
            'total_bookings': total_bookings,
            'total_lots': total_lots,
            'occupancy_rate': round(occupancy_rate, 1),
            'chart_data': chart_data,
            'hourly_trends': hourly_trends,
            'daily_trends': daily_trends,
            'avg_payment': round(float(avg_payment), 0),
            'recent_bookings': serializer.data,
            'stats_by_type': {
                'regular': ParkingSpace.objects.filter(space_type='regular').count(),
                'vip': ParkingSpace.objects.filter(space_type='vip').count(),
            },
            'revenue_by_sector': revenue_by_sector,
            'revenue_by_lot': [
                {'name': item['name'], 'revenue': float(item['total_revenue'] or 0)} 
                for item in revenue_by_lot
            ],
            'lots_occupancy': lots_occupancy
        })

class AdminUserListView(views.APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        # Ensure all users have profiles (safety repair)
        for user in User.objects.filter(profile__isnull=True):
            Profile.objects.get_or_create(user=user)
            
        users = User.objects.annotate(
            booking_count=Count('bookings'),
            total_spent=Sum('bookings__payment__amount', filter=Q(bookings__payment__is_paid=True))
        ).all().order_by('-date_joined')
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

class AdminUserUpdateView(views.APIView):
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
            # Ensure profile exists
            profile, _ = Profile.objects.get_or_create(user=user)
            
            # Simple direct update as this is for admin correction
            profile.phone_number = request.data.get('phone_number', profile.phone_number)
            profile.car_number = request.data.get('car_number', profile.car_number)
            profile.save()
            
            return Response(UserSerializer(user).data)
        except User.DoesNotExist:
            return Response({'error': 'Foydalanuvchi topilmadi'}, status=status.HTTP_404_NOT_FOUND)

class AdminUserToggleActiveView(views.APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
            if user.is_superuser:
                return Response({'error': 'Superuserni bloklab bo\'lmaydi'}, status=status.HTTP_400_BAD_REQUEST)
            
            user.is_active = not user.is_active
            user.save()
            return Response({'status': 'success', 'is_active': user.is_active})
        except User.DoesNotExist:
            return Response({'error': 'Foydalanuvchi topilmadi'}, status=status.HTTP_404_NOT_FOUND)

class AdminExportExcelView(views.APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "SmartPark Daromadlari"

        # Headers
        headers = ["Sana", "Bronlar soni", "Tushum (so'm)"]
        ws.append(headers)

        today = timezone.now().date()
        thirty_days_ago = today - timedelta(days=30)
        
        daily_revenue = Payment.objects.filter(
            is_paid=True, 
            timestamp__date__gte=thirty_days_ago
        ).annotate(date=TruncDate('timestamp')).values('date').annotate(amount=Sum('amount'), count=Count('id')).order_by('date')

        for item in daily_revenue:
            ws.append([item['date'].strftime('%Y-%m-%d'), item['count'], float(item['amount'])])

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=smartpark_hisobot.xlsx'
        return response

class AdminExportPDFView(views.APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()

        elements.append(Paragraph("SmartPark Business Analytics Report", styles['Title']))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Hisobot sanasi: {timezone.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
        elements.append(Spacer(1, 24))

        # Stats Table
        total_revenue = Payment.objects.filter(is_paid=True).aggregate(total=Sum('amount'))['total'] or 0
        total_bookings = Booking.objects.count()
        
        data = [
            ["Ko'rsatkich", "Qiymat"],
            ["Jami tushum", f"{total_revenue:,.0f} so'm"],
            ["Jami bronlar", f"{total_bookings} ta"],
        ]

        t = Table(data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ]))
        elements.append(t)
        
        doc.build(elements)
        buffer.seek(0)
        
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename=smartpark_hisobot.pdf'
        return response
