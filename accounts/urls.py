from django.urls import path
from .views import RegisterAPI, VerifyOTPAPI, LoginAPI
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
urlpatterns = [
    path('register/', RegisterAPI.as_view(), name='register'),
    path('verify-otp/', VerifyOTPAPI.as_view(), name='verify-otp'),
    path('login/', LoginAPI.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]