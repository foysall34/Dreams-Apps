from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from django.utils.translation import gettext_lazy as _
from .models import User

class JWTAuthenticationAllowInactive(JWTAuthentication):
    def authenticate_user(self, validated_token):
        
        # --- ডিবাগিং-এর জন্য এই লাইনটি যোগ করুন ---
        print("\n=======================================================")
        print("✅ SUCCESS: My custom JWTAuthenticationAllowInactive class is being used!")
        print("=======================================================\n")
        
        """
        Overrides the original method to skip the is_active check.
        """
        try:
            user_id = validated_token[self.user_id_field]
        except KeyError:
            raise AuthenticationFailed(_("Token contained no recognizable user identification"), code="token_not_valid")

        try:
            user = self.user_model.objects.get(**{self.user_id_field: user_id})
            # আপনি চাইলে ব্যবহারকারীর তথ্যও প্রিন্ট করে দেখতে পারেন
            print(f"Found user: {user.email}, is_active status: {user.is_active}")
        except self.user_model.DoesNotExist:
            raise AuthenticationFailed(_("User not found"), code="user_not_found")
            
        return user



