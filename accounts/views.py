import random
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from .serializers import ResendOTPSerializer,UserRegisterSerializer, VerifyOTPSerializer, LoginSerializer, PasswordResetConfirmSerializer, PasswordResetRequestSerializer
from .models import User
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import generics
import random
from datetime import timedelta
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model

class RegisterView(APIView):
    permission_classes = [AllowAny] 
    def post(self, request, *args, **kwargs):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Register এর সময় email কে session এ রাখবো
        request.session['pending_email'] = user.email  

        return Response(
            {"detail": "User registered successfully. Please verify OTP."}, 
            status=201
        )


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
    


class PasswordResetRequestAPI(APIView):
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)
            
            # OTP জেনারেট এবং সেভ করুন
            otp = str(random.randint(1000, 9999))
            user.otp = otp
            user.save()

            # ইমেইলে OTP পাঠান
            subject = 'Your Password Reset OTP'
            message = f'Your OTP for password reset is: {otp}'
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [user.email]
            send_mail(subject, message, from_email, recipient_list)

            return Response({
                "message": "Password reset OTP has been sent to your email."
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmAPI(APIView):
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            user = User.objects.get(email=email)
            
            # নতুন পাসওয়ার্ড সেট করুন
            user.set_password(password)
            
            # OTP ব্যবহারের পর মুছে ফেলুন (খুবই গুরুত্বপূর্ণ)
            user.otp = None 
            user.save()

            return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    










# For resend api 
class ResendOTPView(APIView):
    permission_classes = [AllowAny]  # Login না করা user এর জন্য

    def post(self, request, *args, **kwargs):
        serializer = ResendOTPSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "OTP resent successfully."}, status=200)




User = get_user_model()

# OTP পাঠানোর জন্য একটি Helper ফাংশন (ঐচ্ছিক কিন্তু প্রস্তাবিত)
def send_otp_via_email(email, otp):
    """
    এই ফাংশনটি ব্যবহারকারীকে ইমেলের মাধ্যমে OTP পাঠাবে।
    আপনার ইমেল পাঠানোর সার্ভিস (যেমন SendGrid, SMTP) এখানে যুক্ত করুন।
    """
    subject = 'Your Password Reset OTP'
    message = f'Your OTP for password reset is: {otp}'
    from_email = 'your-email@example.com' # আপনার ইমেল ঠিকানা
    recipient_list = [email]
    
    # Django-র ইমেল পাঠানোর ফাংশন ব্যবহার করুন
    # from django.core.mail import send_mail
    # send_mail(subject, message, from_email, recipient_list)
    
    # আপাতত আমরা প্রিন্ট করে রাখছি
    print(f"Sending OTP {otp} to {email}")


class PasswordResetRequestView(generics.GenericAPIView):
    """
    API endpoint to request a password reset. 
    Generates an OTP and sends it to the user's email.
    """
    serializer_class = PasswordResetRequestSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
            # একটি নতুন ৪-সংখ্যার OTP তৈরি করুন
            otp = str(random.randint(1000, 9999))
            
            # ব্যবহারকারীর অ্যাকাউন্টে নতুন OTP সংরক্ষণ করুন
            user.otp = otp
            user.save()
            
            # ব্যবহারকারীকে ইমেলের মাধ্যমে OTP পাঠান
            send_otp_via_email(user.email, otp)
            
            return Response(
                {"message": "An OTP has been sent to your email."}, 
                status=status.HTTP_200_OK
            )
            
        except User.DoesNotExist:
            # সিরিয়ালাইজার এটি হ্যান্ডেল করলেও, একটি অতিরিক্ত সুরক্ষা স্তর রাখা ভালো
            return Response(
                {"error": "User with this email does not exist."}, 
                status=status.HTTP_404_NOT_FOUND
            )

class ResendOTPViewforPassword(generics.GenericAPIView):
    """
    API endpoint to resend OTP for password reset.
    """
    serializer_class = ResendOTPSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
            # একটি নতুন ৪-সংখ্যার OTP তৈরি করুন
            new_otp = str(random.randint(1000, 9999))
            
            # ব্যবহারকারীর অ্যাকাউন্টে নতুন OTP সংরক্ষণ করুন
            user.otp = new_otp
            user.save()
            
            # ব্যবহারকারীকে ইমেলের মাধ্যমে নতুন OTP পাঠান
            send_otp_via_email(user.email, new_otp)
            
            return Response(
                {"message": "A new OTP has been sent to your email."}, 
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {"error": "User with this email does not exist."}, 
                status=status.HTTP_404_NOT_FOUND
            )

class PasswordResetConfirmView(generics.GenericAPIView):
    """
    API endpoint to confirm password reset with OTP and new password.
    """
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # সিরিয়ালাইজার ভ্যালিডেশনের সময় ব্যবহারকারীকে 'attrs'-এ যুক্ত করেছে
        user = serializer.validated_data['user']
        new_password = serializer.validated_data['password']
        
        # নতুন পাসওয়ার্ড সেট করুন (set_password ব্যবহার করলে পাসওয়ার্ড হ্যাশ হয়ে যাবে)
        user.set_password(new_password)
        
        # OTP ব্যবহার হয়ে গেলে তা মুছে ফেলুন
        user.otp = None 
        user.save()
        
        return Response(
            {"message": "Password has been reset successfully."}, 
            status=status.HTTP_200_OK
        )