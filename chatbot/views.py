

# your_app/views.py

from datetime import datetime, time
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated , AllowAny
from django.contrib.auth import get_user_model

# Make sure to import your models and services
from .models import Dream, Subscription  , Pricing
from .serializers import DreamInterpretationSerializer , DreamHistorySerializer , PricingSerializer , AudioGenerationSerializer
from .import dream_interpreter, voice_services 


User = get_user_model()

class DreamInterpretationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = DreamInterpretationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        dream_text = validated_data['text']
        user = request.user
        answers = validated_data.get('answers')

        user_plan = 'premium'
 
        plan_features = {
            'free':     {'daily_limit': 20, 'question_count': 2, 'has_audio': False}, 
            'premium':  {'daily_limit': 30, 'question_count': 5, 'has_audio': False},
            'platinum': {'daily_limit': 30, 'question_count': 1, 'has_audio': False} 
        }

        current_plan_features = plan_features.get(user_plan, plan_features['free'])

        dream, created = Dream.objects.get_or_create(user=user, text=dream_text)

        if answers:
            if dream.status != 'initial' or not dream.interpretation:
                return Response(
                    {"error": "Initial interpretation must be generated before submitting answers."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            ultimate_interpretation = dream_interpreter.generate_ultimate_interpretation(
                user.id, dream_text, answers
            )
            
            audio_url = None
           
            if current_plan_features['has_audio']:
                audio_url = voice_services.text_to_voice_elevenlabs(
                    text=ultimate_interpretation,
                    user_id=user.id,
                    voice_choice='Soothing_female'
                )

            dream.answers = answers
            dream.ultimate_interpretation = ultimate_interpretation
            dream.status = 'completed'
            dream.save()

            response_data = {
                "interpretation": ultimate_interpretation,
                "ans_type": "ultimate_ans",
                "audio_url": request.build_absolute_uri(audio_url) if audio_url else None
            }
            return Response(response_data, status=status.HTTP_200_OK)

       
        if not created and dream.status == 'initial':
            return Response(
                {"error": "This dream has already been interpreted. Please provide answers to proceed."},
                status=status.HTTP_400_BAD_REQUEST
            )

      
        today_min = timezone.make_aware(datetime.combine(timezone.now().date(), time.min))
        today_max = timezone.make_aware(datetime.combine(timezone.now().date(), time.max))
        dreams_today_count = Dream.objects.filter(user=user, created_at__range=(today_min, today_max)).count()

        if dreams_today_count >= current_plan_features['daily_limit']:
            if created:
                dream.delete()
            return Response(
                {"error": f"You have reached your daily limit of {current_plan_features['daily_limit']} dream(s) for the '{user_plan}' plan."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        interpretation, questions = dream_interpreter.generate_interpretation(
            user.id, dream_text, current_plan_features['question_count']
        )
        
        audio_url = None
   
        if current_plan_features['has_audio']:
            audio_response_text = f"{interpretation}\n\nHere are some questions to consider:\n{' '.join(questions)}"
            audio_url = voice_services.text_to_voice_elevenlabs(
                text=audio_response_text,
                user_id=user.id,
                voice_choice='Soothing_female'
            )

        dream.interpretation = interpretation
        dream.questions = questions
        dream.status = 'initial'
        dream.save()

        response_data = {
            "text": dream_text,
            "interpretation": interpretation,
            "questions": questions,
            "audio_url": request.build_absolute_uri(audio_url) if audio_url else None,
            "ans_type": "interpretation"
        }
        return Response(response_data, status=status.HTTP_201_CREATED)



# For audio generation and voice services
class AudioGenerateView(APIView):
    """
    An endpoint to generate audio from user-provided text.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests to generate audio from text.
        Requires:
        - 'text': string
        - 'user_type': 'free' | 'premium' | 'platinum'
        - 'voice_type': optional, e.g. 'Soothing_female'
        """
        serializer = AudioGenerationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        text = validated_data['text']
        user_type = validated_data.get('user_type', 'free')
        voice_type = validated_data.get('voice_type', 'Soothing_female')
        user = request.user

        # Define plan features (you can extend later)
        plan_features = {
            'free':     {'has_audio': True},
            'premium':  {'has_audio': True},
            'platinum': {'has_audio': True},
        }

        # Get user plan feature
        current_plan = plan_features.get(user_type, plan_features['free'])

        audio_url = None
   
        if current_plan['has_audio']:
            audio_url = voice_services.text_to_voice_elevenlabs(
                text=text,
                user_id=user.id,
                voice_choice=voice_type
            )

      
        response_data = {
            "text": text,
            "user_type": user_type,
            "voice_type": voice_type,
            "audio_url": request.build_absolute_uri(audio_url) if audio_url else None
        }
        return Response(response_data, status=status.HTTP_201_CREATED)


# Types of voice 
class VoiceTypeListView(APIView):
    """
    An endpoint to retrieve a list of all available voice types for audio generation.
    """
    permission_classes = [AllowAny] # Or AllowAny if you want it to be public

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests to return the list of available voice types.
        """
        # You should replace this with your actual list of available voices
        # from your voice generation service.
        available_voices = [
            'Soothing_female',
            'Calm_male',
            'Deep_narrator',
            'Upbeat_female',
            'Standard_male',
            'Gentle_female',
            'Authoritative_male'
        ]

        response_data = {
            "available_voice_types": available_voices
        }
        return Response(response_data, status=status.HTTP_200_OK)









# For store History 

class DreamHistoryView(generics.ListAPIView):
   
    permission_classes = [IsAuthenticated]
    serializer_class = DreamHistorySerializer

    def get_queryset(self):

        user = self.request.user
        return Dream.objects.filter(user=user).order_by('-created_at')

class DreamDetailView(generics.RetrieveAPIView):

    permission_classes = [IsAuthenticated]
    serializer_class = DreamHistorySerializer
    queryset = Dream.objects.all()

    def get_queryset(self):
    
        user = self.request.user
        return Dream.objects.filter(user=user)
    


# Stripe Payment Gateway 


import stripe
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Subscription
from django.urls import reverse
from .models import Subscription

User = get_user_model()
stripe.api_key = settings.STRIPE_SECRET_KEY


class CreateCheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        pricing_id = request.data.get('pricing_id')

        if not pricing_id:
            return Response(
                {"error": "pricing_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            pricing_plan = Pricing.objects.get(id=pricing_id)

            success_url = request.build_absolute_uri(reverse('success'))
            cancel_url = request.build_absolute_uri(reverse('cancel'))

            session = stripe.checkout.Session.create(
                mode='subscription',
                line_items=[{
                    "price": pricing_plan.stripe_price_id,
                    "quantity": 1,
                }],
                customer_email=request.user.email,
                success_url=success_url,
                cancel_url=cancel_url,

                metadata={
                    "user_id": request.user.id,
                    "pricing_id": pricing_plan.id,
                    "plan_type": pricing_plan.plan_type,
                    "billing_interval": pricing_plan.billing_interval,
                }
            )

            return Response({"checkout_url": session.url})

        except Pricing.DoesNotExist:
            return Response(
                {"error": "Pricing plan not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )




from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):

    def post(self, request, *args, **kwargs):
        print("\n--- [Webhook] Request Received ---")

        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except Exception as e:
            print("[Webhook] ⚠ Error validating event:", e)
            return Response(status=400)

        event_type = event.get("type")
        print(f"[Webhook] Event Type: {event_type}")

    
        if event_type == "checkout.session.completed":
            session = event["data"]["object"]
            metadata = session.get("metadata", {})
            print(f"[Webhook] Metadata: {metadata}")

            user_id = metadata.get("user_id")
            pricing_id = metadata.get("pricing_id")

            if not user_id or not pricing_id:
                print("[Webhook]  Missing required metadata")
                return Response(status=400)

            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                print("[Webhook]  User not found in DB")
                return Response(status=404)

            try:
                pricing_plan = Pricing.objects.get(id=pricing_id)
            except Pricing.DoesNotExist:
                print("[Webhook]  Pricing plan not found in DB")
                return Response(status=404)

            subscription_id = session.get("subscription")
            customer_id = session.get("customer")

            Subscription.objects.update_or_create(
                user=user,
                defaults={
                    "stripe_customer_id": customer_id,
                    "stripe_subscription_id": subscription_id,
                    "plan": pricing_plan.plan_type,
                    "is_active": True,
                }
            )

            print(f"[Webhook] Subscription updated for {user.email}: {pricing_plan}")

       
        elif event_type == "customer.subscription.deleted":
            subscription_obj = event["data"]["object"]
            user_email = subscription_obj.get("customer_email")

            try:
                user = User.objects.get(email=user_email)
                Subscription.objects.filter(user=user).update(is_active=False)
                print(f"[Webhook] 🚫 Subscription canceled for {user.email}")
            except:
                pass

        return Response(status=200)



from django.views.generic import TemplateView
from django.views.generic import TemplateView

class SuccessView(TemplateView):
    template_name = 'success.html'

    def get_context_data(self, **kwargs):
   
        context = super().get_context_data(**kwargs)
    
        context['message'] = "Payment Successful!"
        context['details'] = "Thank you for your purchase. Your payment has been processed successfully."
        
        
        return context

class CancelView(TemplateView):
    template_name = 'cancel.html'

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status





class PricingListAPIView(APIView):
 
    def get(self, request, format=None):

        plans = Pricing.objects.all()
  
        serializer = PricingSerializer(plans, many=True)
        return Response(serializer.data)




from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Pricing
from .serializers import PricingMinimalSerializer


class PricingMinimalView(APIView):
    def get(self, request):
        plans = Pricing.objects.all()
        serializer = PricingMinimalSerializer(plans, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
