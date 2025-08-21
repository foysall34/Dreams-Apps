from django.urls import path
from .views import RegisterView, VerifyOTPAPI, LoginAPI , PasswordResetConfirmAPI, PasswordResetRequestAPI ,ResendOTPView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    
    
)
urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-otp/', VerifyOTPAPI.as_view(), name='verify-otp'),
    path('login/', LoginAPI.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('password-reset/request/', PasswordResetRequestAPI.as_view(), name='password-reset-request'),
    path('password-reset/confirm/', PasswordResetConfirmAPI.as_view(), name='password-reset-confirm'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
]