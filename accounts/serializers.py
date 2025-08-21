from rest_framework import serializers
from .models import User
from rest_framework_simplejwt.tokens import RefreshToken
import random
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail



class UserRegisterSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)
    tokens = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password', 'password2', 'tokens']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def get_tokens(self, user):
        """
        রেসপন্সে দেখানোর জন্য টোকেন তৈরি করে।
        """
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        attrs.pop('password2')
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        user.is_active = False  # Initially account will be inactive

        # OTP generation logic
        otp = random.randint(100000, 999999)
        otp_expiry = timezone.now() + timedelta(minutes=10)

        user.otp = otp
        user.otp_expiry = otp_expiry
        user.save()

        # Send OTP email (without including the OTP in the email body)
        send_mail(
            'Verify your account',
            'Please check your app to get the OTP.',
            'from@example.com',  # Replace with your email
            [user.email],
            fail_silently=False,
        )
        
        # Return the user object after creating
        return user

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=4)

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'})




class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value

class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=4)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        try:
            user = User.objects.get(email=attrs['email'])
            if user.otp != attrs['otp']:
                raise serializers.ValidationError({"otp": "Invalid OTP."})
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "User with this email does not exist."})

        return attrs
    

# **************************************************************** REsend Otp **********************************************
class ResendOTPSerializer(serializers.Serializer):
    def validate(self, attrs):
        request = self.context.get("request")
        email = request.session.get("pending_email")  # Session থেকে email নাও

        if not email:
            raise serializers.ValidationError({"detail": "No pending registration found."})

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "This email is not registered."})

       

        self.user = user
        return attrs

    def save(self):
        user = self.user

        # ✅ ৪ digit OTP generate করো
        otp = random.randint(1000, 9999)


        user.otp = str(otp)
        user.save()

        # ✅ ইমেইল পাঠাও (OTP + custom message)
        message = f"""
        Dear {user.first_name or 'User'},

        Your One Time Password (OTP) is: {otp}
        This OTP will expire in 1 minutes.

        If you did not request this, please ignore this email.

        Regards,
        Dream Apps Team
        """

        send_mail(
            'Dream Apps - OTP Verification',
            message,
            'from@example.com',  # sender email address
            [user.email],
            fail_silently=False,
        )

        return otp


    

