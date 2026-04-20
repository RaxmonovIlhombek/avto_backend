from rest_framework import views, permissions, status
from rest_framework.response import Response
from .serializers import UserSerializer, RegisterSerializer
from django.contrib.auth.models import User

class RegisterView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from rest_framework.authtoken.models import Token
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                "token": token.key,
                "user": UserSerializer(user).data,
                "message": "Foydalanuvchi muvaffaqiyatli yaratildi"
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(views.APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        from django.contrib.auth import authenticate
        from rest_framework.authtoken.models import Token
        
        username = request.data.get("username")
        password = request.data.get("password")
        
        user = authenticate(username=username, password=password)
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                "token": token.key,
                "user": UserSerializer(user).data
            })
        return Response({"error": "Login yoki parol noto'g'ri"}, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        # Profil ma'lumotlarini (moshina raqami, telefon) yangilash
        user = request.user
        profile_data = request.data.get('profile', {})
        
        if profile_data:
            profile = user.profile
            profile.phone_number = profile_data.get('phone_number', profile.phone_number)
            profile.car_number = profile_data.get('car_number', profile.car_number)
            profile.save()
            
        return Response(UserSerializer(user).data)
