import random
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from .serializers import PlanTypeSerializers,ResendOTPSerializer,  UserTypeUpdateSerializer ,UserRegisterSerializer, VerifyOTPSerializer,LoginSerializer,  PasswordResetConfirmSerializer, PasswordResetRequestSerializer
from .models import User
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import generics,permissions
import random
from datetime import timedelta
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model


class UserProfileTypeView(generics.RetrieveUpdateAPIView):
  
    queryset = User.objects.all()
    serializer_class = PlanTypeSerializers
    permission_classes = [permissions.IsAuthenticated]


    def get_object(self):
        """
        This view should return an object for the currently authenticated user.
        """
        return self.request.user




class UserRegisterView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save() 
            return Response({
                "message": "OTP has been sent to your email. Please verify to complete registration."
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class VerifyOTPView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save() 
            
        
            refresh = RefreshToken.for_user(user)
            tokens = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
            
            return Response({
                "message": "Account verified successfully.",
                "tokens": tokens,
                "user": {
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                }
            }, status=status.HTTP_201_CREATED)

class LoginAPI(APIView):
    """
    Handles user login and user type updates.
    """
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        Login (POST) should be allowed for any user.
        """
        if self.request.method == 'POST':
            return []
        return super().get_permissions()

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user = authenticate(username=email, password=password)

            if user is not None:
                if user.is_active:
                    refresh = RefreshToken.for_user(user)
                    return Response({
                        "message": "Login successful.",
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                        "user_info": {
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                            "email": user.email,
                            "user_type": user.user_type,
                        }
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({"error": "Account not verified."}, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        """
        Handles partial updates to the user, specifically for the user_type field.
        """
        user = request.user
        serializer = UserTypeUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "User type updated successfully.",
                "user_info": serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestAPI(APIView):
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)
     
            otp = str(random.randint(1000, 9999))
            user.otp = otp
            user.save()

   
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
            
      
            user.set_password(password)
            

            user.save()

            return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    










# For resend api 
class ResendOTPView(APIView):
    permission_classes = [AllowAny]  

    def post(self, request, *args, **kwargs):
        serializer = ResendOTPSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "OTP resent successfully."}, status=200)




User = get_user_model()


def send_otp_via_email(email, otp):

    subject = 'Your Password Reset OTP'
    message = f'Your OTP for password reset is: {otp}'
    from_email = 'your-email@example.com'
    recipient_list = [email]
    


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
  
            otp = str(random.randint(1000, 9999))
            
            user.otp = otp
            user.save()
            
            send_otp_via_email(user.email, otp)
            
            return Response(
                {"message": "An OTP has been sent to your email."}, 
                status=status.HTTP_200_OK
            )
            
        except User.DoesNotExist:

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

            new_otp = str(random.randint(1000, 9999))
            

            user.otp = new_otp
            user.save()
            

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
        
        user = serializer.validated_data['user']
        new_password = serializer.validated_data['password']
    
        user.set_password(new_password)
        user.otp = None 
        user.save()
        
        return Response(
            {"message": "Password has been reset successfully."}, 
            status=status.HTTP_200_OK
        )