import random
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from .serializers import UserRegisterSerializer, VerifyOTPSerializer, LoginSerializer
from .models import User
from rest_framework_simplejwt.tokens import RefreshToken


class RegisterAPI(APIView):
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # OTP জেনারেট এবং সেভ করুন
            otp = str(random.randint(1000, 9999))
            user.otp = otp
            user.save()

            # ইমেইলে OTP পাঠান
            subject = 'Your OTP for account verification'
            message = f'Your OTP is: {otp}'
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [user.email]
            send_mail(subject, message, from_email, recipient_list)

            return Response({
                "message": "Registration successful! Please check your email for OTP."
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyOTPAPI(APIView):
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']

            try:
                user = User.objects.get(email=email)
                if user.otp == otp:
                    user.is_active = True
                    user.otp = None # OTP ব্যবহারের পর মুছে ফেলা হলো
                    user.save()
                    return Response({"message": "Account verified successfully."}, status=status.HTTP_200_OK)
                else:
                    return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginAPI(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user = authenticate(username=email, password=password)

            if user is not None:
                if user.is_active:
                    # আগের টোকেন জেনারেশন কোড মুছে নতুন কোড যুক্ত করুন
                    refresh = RefreshToken.for_user(user)
                    
                    return Response({
                        "message": "Login successful.",
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                        "user_info": {
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                            "email": user.email
                        }
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({"error": "Account not verified."}, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)