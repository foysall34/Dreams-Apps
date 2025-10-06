

# your_app/views.py

from datetime import datetime, time
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
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
            'platinum': {'daily_limit': 30, 'question_count': 7, 'has_audio': False} 
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
    An endpoint to generate audio from text, providing interpretation and questions.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests to generate audio and interpretation.

        Requires 'text' and 'user_type' in the request data.
        'voice_type' is optional.
        """
        serializer = AudioGenerationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        text = validated_data['text']
        user_type = validated_data['user_type']
        voice_type = validated_data.get('voice_type', 'Soothing_female')
        user = request.user

        # Define plan features for different user types
        plan_features = {
            'free':     {'question_count': 2, 'has_audio': True},
            'premium':  {'question_count': 5, 'has_audio': True},
            'platinum': {'question_count': 7, 'has_audio': True}
        }

        current_plan_features = plan_features.get(user_type, plan_features['free'])

        # Generate interpretation and questions
        interpretation, questions = dream_interpreter.generate_interpretation(
            user.id, text, current_plan_features['question_count']
        )

        audio_url = None
        # Generate audio if the user's plan has audio features
        if current_plan_features['has_audio']:
            audio_response_text = f"{interpretation}\n\nHere are some questions to consider:\n{' '.join(questions)}"
            audio_url = voice_services.text_to_voice_elevenlabs(
                text=audio_response_text,
                user_id=user.id,
                voice_choice=voice_type
            )

        # Prepare the response data
        response_data = {
            "text": text,
            "interpretation": interpretation,
            "questions": questions,
            "audio_url": request.build_absolute_uri(audio_url) if audio_url else None
        }
        return Response(response_data, status=status.HTTP_201_CREATED)


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
 
        subscription_type = request.data.get('subscription_type')

        price_id = settings.STRIPE_PRICE_IDS.get(subscription_type)

   
        if not price_id:
            return Response(
                {"error": "Invalid or missing subscription_type."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            success_url = request.build_absolute_uri(reverse('success'))
            cancel_url = request.build_absolute_uri(reverse('cancel'))

            checkout_session = stripe.checkout.Session.create(
                line_items=[
                    {
                        'price': price_id,  
                        'quantity': 1,
                    },
                ],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=request.user.email,
                metadata={
                    'user_id': request.user.id,
        
                    'subscription_type': subscription_type
                }
            )
            return Response({'sessionId': checkout_session.url})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    def post(self, request, *args, **kwargs):

        
        print("\n--- [Debug] Webhook request received! ---")

        webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        event = None

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except ValueError as e:
            # --- [Debug 2] ---
            # If the payload is invalid
            print(f" [Debug] Invalid Payload! Error: {str(e)}")
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError as e:
            # --- [Debug 3] ---
            # If the Webhook Secret Key does not match
            print(f" [Debug] Signature verification failed! Check your STRIPE_WEBHOOK_SECRET. Error: {str(e)}")
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # --- [Debug 4] ---
        # See which type of event was received
        print(f"✅ [Debug] Event constructed successfully. Type: {event['type']}")

        if event['type'] == 'checkout.session.completed':
            print("--- [Debug] Handling 'checkout.session.completed' event ---")
            session = event['data']['object']
            
            metadata = session.get('metadata', {})
            # --- [Debug 5] ---
            # Print the entire metadata object to see what's inside
            print(f"[Debug] Received Metadata: {metadata}")
            
            user_id = metadata.get('user_id')
            print(f"[Debug] Retrieved user_id: {user_id}") # Your previous print
            
            subscription_type = metadata.get('subscription_type')
            print(f"[Debug] Retrieved subscription_type: {subscription_type}") # Your previous print

            if not user_id or not subscription_type:
                print("[Debug] user_id or subscription_type not found in metadata.")
                return Response({"error": "User ID or subscription_type not in session metadata"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                user = User.objects.get(id=user_id)
                # --- [Debug 6] ---
                # Confirm that the user was found in the database
                print(f"✅ [Debug] User '{user.username}' (ID: {user.id}) found in the database.")
            except User.DoesNotExist:
                # --- [Debug 7] ---
                # If the user could not be found
                print(f"[Debug] User with ID: {user_id} was not found in the database.")
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            
            # --- [Debug 8] ---
            # Just before the database operation
            print("[Debug] Calling Subscription.objects.update_or_create...")
            
            Subscription.objects.update_or_create(
                user=user,
                defaults={
                    'stripe_customer_id': session.customer,
                    'stripe_subscription_id': session.subscription,
                    'plan': subscription_type,  
                    'is_active': True
                }
            )
   
            # --- [Debug 9] ---
            # After a successful database update
            print(f"✅ [Debug] Successfully created/updated plan to '{subscription_type}' for user '{user.username}'.")

        # You can also log other events if you need to
        # else:
        #     print(f"--- [Debug] Received event '{event['type']}' but it is not being handled. ---")
      
        return Response(status=status.HTTP_200_OK)


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



