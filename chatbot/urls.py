from django.urls import path

from .views import DreamInterpretationView, DreamHistoryView , DreamDetailView
urlpatterns = [
  
  path('dream/' , DreamInterpretationView.as_view() , name= "done"),
  path('history/', DreamHistoryView.as_view(), name='dream-history'),
  path('history/<int:pk>/', DreamDetailView.as_view(), name='dream-detail'),

]