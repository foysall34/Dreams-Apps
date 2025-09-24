from django.urls import path

from .views import DreamInterpretationView
urlpatterns = [
  
  path('dream/' , DreamInterpretationView.as_view() , name= "done")
]