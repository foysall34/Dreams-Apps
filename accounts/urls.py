from django.urls import path
from .views import UserProfileTypeView,UserRegisterView, VerifyOTPView, LoginAPI , PasswordResetConfirmAPI, PasswordResetRequestAPI ,ResendOTPView,ResendOTPViewforPassword
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    
    
)
urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='register'),
    path('details/', UserProfileTypeView.as_view(), name='details'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('login/', LoginAPI.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('password-reset/request/', PasswordResetRequestAPI.as_view(), name='password-reset-request'),
    path('password-reset/confirm/', PasswordResetConfirmAPI.as_view(), name='password-reset-confirm'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
    path('password-reset/resend-otp/', ResendOTPViewforPassword.as_view(), name='password-reset-resend-otp'),
]