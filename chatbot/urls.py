from django.urls import path

from .views import DreamInterpretationView, DreamHistoryView , DreamDetailView , CreateCheckoutSessionView , StripeWebhookView
urlpatterns = [
  
  path('dream/' , DreamInterpretationView.as_view() , name= "done"),
  path('history/', DreamHistoryView.as_view(), name='dream-history'),
  path('history/<int:pk>/', DreamDetailView.as_view(), name='dream-detail'),
  path('create-checkout-session/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
  path('stripe-webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),

]