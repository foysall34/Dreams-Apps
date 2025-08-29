# chatbot/urls.py

from django.urls import path
from .views import DreamInterpretationAPIView , DreamInterpretationView, InterpretDreamView

urlpatterns = [
    path('interpret/', DreamInterpretationAPIView.as_view(), name='interpret-dream'),
    path('interpret2/', DreamInterpretationView.as_view(), name='dream-interpretation'),
    path('deepseek/', DreamInterpretationAPIView.as_view(), name='deepseek'),
    path('voice/', InterpretDreamView.as_view(), name='interpret-dream'),
]