from rest_framework import serializers
from .models import User
from rest_framework_simplejwt.tokens import RefreshToken
import random
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.contrib.auth import get_user_model


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



# ************************************forget password ***********************
User = get_user_model()

class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for initiating a password reset request.
    Validates that the provided email exists in the system.
    """
    email = serializers.EmailField(
        max_length=254,  # standard max length for email
        required=True,
        help_text="Enter the email address associated with your account."
    )

    def validate_email(self, value):
        """
        Validates that a user with the provided email exists.
        """
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value

class ResendOTPSerializer(serializers.Serializer):
    """
    Serializer for resending the OTP for password reset.
    Validates that the provided email exists in the system.
    """
    email = serializers.EmailField(
        max_length=254,
        required=True,
        help_text="Enter the email address to resend the OTP to."
    )

    def validate_email(self, value):
        """
        Validates that a user with the provided email exists.
        """
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value

class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming a password reset with OTP and new password.
    """
    email = serializers.EmailField(
        max_length=254,
        required=True,
        help_text="Enter your email address."
    )
    otp = serializers.CharField(
        max_length=4,
        min_length=4,
        required=True,
        help_text="Enter the 4-digit OTP received."
    )
    password = serializers.CharField(
        write_only=True,  # This field will not be readable
        style={'input_type': 'password'},
        required=True,
        help_text="Enter your new password."
    )
    password2 = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        required=True,
        help_text="Confirm your new password."
    )

    def validate(self, attrs):
        """
        Validates the OTP and checks if the passwords match.
        """
        email = attrs.get('email')
        otp_entered = attrs.get('otp')
        password = attrs.get('password')
        password2 = attrs.get('password2')

        # Check if passwords match
        if password and password2 and password != password2:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        # Validate OTP and user existence
        try:
            user = User.objects.get(email=email)
            # Assuming your User model has an 'otp' field to store the OTP
            if not user.otp or user.otp != otp_entered:
                raise serializers.ValidationError({"otp": "Invalid or expired OTP."})
        except User.DoesNotExist:
            # This case should ideally be caught by validate_email in PasswordResetRequestSerializer
            # or ResendOTPSerializer if called first, but good to have here too for direct use.
            raise serializers.ValidationError({"email": "User with this email does not exist."})
        except AttributeError:
             # Handle case where User model might not have 'otp' field
            raise serializers.ValidationError({"otp": "OTP functionality not available for this user model."})

        # Add a check for OTP expiration if you implement that feature
        # For example: if user.otp_expires_at < timezone.now(): raise serializers.ValidationError({"otp": "OTP has expired."})

        attrs['user'] = user # Make the user object available for the view
        return attrs

# **************************************************************** REsend Otp **********************************************
class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate(self, attrs):
        email = attrs.get('email')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "This email is not registered."})

       

        self.user = user
        return attrs

    def save(self):
        user = self.user

        # Generate 4-digit OTP
        otp = random.randint(1000, 9999)
      
        user.otp = str(otp)
        user.save()

        # Send OTP email
        message = f"""
        Dear {user.first_name or 'User'},

        Your One Time Password (OTP) is: {otp}
        It will expire in 10 minutes.

        If you did not request this, please ignore this email.

        Regards,
        Dream Apps Team
        """

        send_mail(
            'Dream Apps - OTP Verification',
            message,
            'from@example.com',
            [user.email],
            fail_silently=False,
        )

        return otp


    

