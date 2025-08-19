# chatbot/urls.py

from django.urls import path
from .views import DreamInterpretationAPIView , DreamInterpretationView

urlpatterns = [
    path('interpret/', DreamInterpretationAPIView.as_view(), name='interpret-dream'),
    path('interpret2/', DreamInterpretationView.as_view(), name='dream-interpretation'),
]