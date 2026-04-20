from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ParkingSpaceViewSet, BookingViewSet, PaymentViewSet, ParkingLotViewSet, CustomerStatsView
from .views_auth import RegisterView, LoginView, UserProfileView
from .views_admin import (
    AdminStatsView, AdminUserListView, AdminUserToggleActiveView,
    AdminUserUpdateView, AdminExportExcelView, AdminExportPDFView
)
from .views_notifications import NotificationListView, NotificationMarkReadView, NotificationMarkAllReadView

router = DefaultRouter()
router.register(r'lots', ParkingLotViewSet)
router.register(r'spaces', ParkingSpaceViewSet)
router.register(r'bookings', BookingViewSet, basename='bookings')
router.register(r'payments', PaymentViewSet, basename='payments')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/profile/', UserProfileView.as_view(), name='profile'),
    path('customer/stats/', CustomerStatsView.as_view(), name='customer_stats'),
    
    # Admin
    path('admin/stats/', AdminStatsView.as_view(), name='admin_stats'),
    path('admin/users/', AdminUserListView.as_view(), name='admin_users'),
    path('admin/users/<int:pk>/', AdminUserUpdateView.as_view(), name='admin_user_update'),
    path('admin/users/<int:pk>/toggle/', AdminUserToggleActiveView.as_view(), name='admin_user_toggle'),
    path('admin/export/excel/', AdminExportExcelView.as_view(), name='admin_export_excel'),
    path('admin/export/pdf/', AdminExportPDFView.as_view(), name='admin_export_pdf'),
    
    # Notifications
    path('notifications/', NotificationListView.as_view(), name='notifications'),
    path('notifications/<int:pk>/read/', NotificationMarkReadView.as_view(), name='notification_read'),
    path('notifications/read-all/', NotificationMarkAllReadView.as_view(), name='notifications_read_all'),
]
