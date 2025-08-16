# chatbot/urls.py

from django.urls import path
from .views import DreamInterpretationAPIView

urlpatterns = [
    path('interpret/', DreamInterpretationAPIView.as_view(), name='interpret-dream'),
]