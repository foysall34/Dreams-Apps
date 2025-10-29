from django.urls import path

from .views import  PricingMinimalView,VoiceTypeListView,AudioGenerateView,PricingListAPIView,DreamInterpretationView, DreamHistoryView , DreamDetailView , CreateCheckoutSessionView , StripeWebhookView , SuccessView , CancelView




urlpatterns = [
  path('pricing/', PricingListAPIView.as_view(), name='pricing-list'),
  path('dream/' , DreamInterpretationView.as_view() , name= "done"),
  path('history/', DreamHistoryView.as_view(), name='dream-history'),
  path('history/<int:pk>/', DreamDetailView.as_view(), name='dream-detail'),
  path('create-checkout-session/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
  path('webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
  path('success/', SuccessView.as_view(), name='success'),
  path('cancel/', CancelView.as_view(), name='cancel'),
  path('audio-generate/', AudioGenerateView.as_view(), name='audio-generate'),
  path('voice-types/', VoiceTypeListView.as_view(), name='voice-type-list'),
  path('pricing-minimal/', PricingMinimalView.as_view(), name="pricing-minimal"),


]