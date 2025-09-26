

# your_app/views.py

from datetime import datetime, time
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model

# Make sure to import your models and services
from .models import Dream, Subscription 
from .serializers import DreamInterpretationSerializer , DreamHistorySerializer
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

        try:
            subscription = Subscription.objects.get(user=user, is_active=True)
            user_plan = subscription.plan
        except Subscription.DoesNotExist:
            user_plan = 'free'
            
        # =================================================================
        # START: The only change you need is here
        # =================================================================
        plan_features = {
            'free':     {'daily_limit': 20, 'question_count': 2, 'has_audio': False}, # <-- পরিবর্তন
            'premium':  {'daily_limit': 30, 'question_count': 5, 'has_audio': True}, # <-- পরিবর্তন
            'platinum': {'daily_limit': 30, 'question_count': 7, 'has_audio': True}   # <-- এটি True থাকবে
        }
        # =================================================================
        # END: The change is complete
        # =================================================================

        current_plan_features = plan_features.get(user_plan, plan_features['free'])

        dream, created = Dream.objects.get_or_create(user=user, text=dream_text)

        # Logic for when a user submits answers to previous questions
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
            # This 'if' condition will now only be true for platinum users
            if current_plan_features['has_audio']:
                print(user_plan)
                audio_url = voice_services.text_to_voice_elevenlabs(
                    text=ultimate_interpretation,
                    user_id=user.id,
                    voice_choice='soothing_female'
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

        # Block re-submission if initial interpretation already exists
        if not created and dream.status == 'initial':
            return Response(
                {"error": "This dream has already been interpreted. Please provide answers to proceed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Daily Limit Enforcement
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

        # Generate the initial interpretation and questions
        interpretation, questions = dream_interpreter.generate_interpretation(
            user.id, dream_text, current_plan_features['question_count']
        )
        
        audio_url = None
        # This 'if' condition will now only be true for platinum users
        if current_plan_features['has_audio']:
            audio_response_text = f"{interpretation}\n\nHere are some questions to consider:\n{' '.join(questions)}"
            audio_url = voice_services.text_to_voice_elevenlabs(
                text=audio_response_text,
                user_id=user.id,
                voice_choice='soothing_female'
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
# your_app/views.py

import stripe
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Subscription

stripe.api_key = settings.STRIPE_SECRET_KEY

class CreateCheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        price_id = request.data.get('price_id')
        try:
            checkout_session = stripe.checkout.Session.create(
                line_items=[
                    {
                        'price': price_id,
                        'quantity': 1,
                    },
                ],
                mode='subscription',
                success_url=settings.FRONTEND_CHECKOUT_SUCCESS_URL,
                cancel_url=settings.FRONTEND_CHECKOUT_CANCEL_URL,
                customer_email=request.user.email,
                metadata={
                    'user_id': request.user.id
                }
            )
            return Response({'sessionId': checkout_session.id})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StripeWebhookView(APIView):
    """
    Handles incoming webhooks from Stripe to update user subscriptions.
    """
    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        event = None

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            # Invalid payload
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # =================================================================
        # START: Handle the checkout.session.completed event
        # =================================================================
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            
            # Retrieve user_id from metadata
            user_id = session.get('metadata', {}).get('user_id')
            if not user_id:
                return Response({"error": "User ID not in session metadata"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

            # Retrieve the price ID from the line items
            try:
                line_items = stripe.checkout.Session.list_line_items(session.id, limit=1)
                price_id = line_items.data[0].price.id
            except Exception as e:
                return Response({"error": f"Could not retrieve price ID: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

            # Map price_id to plan name
            new_plan = None
            if price_id == settings.STRIPE_PREMIUM_PRICE_ID:
                new_plan = 'premium'
            elif price_id == settings.STRIPE_PLATINUM_PRICE_ID:
                new_plan = 'platinum'
            
            if not new_plan:
                return Response({"error": f"Price ID {price_id} not configured"}, status=status.HTTP_400_BAD_REQUEST)

            # Update or create the subscription for the user
            Subscription.objects.update_or_create(
                user=user,
                defaults={
                    'stripe_customer_id': session.customer,
                    'stripe_subscription_id': session.subscription,
                    'plan': new_plan,
                    'is_active': True
                }
            )
            print(f"Successfully updated plan to '{new_plan}' for user {user.username}")

        # =================================================================
        # END: Handle the checkout.session.completed event
        # =================================================================

        # Handle other events like subscription cancellation
        if event['type'] == 'customer.subscription.deleted':
            subscription_id = event['data']['object']['id']
            try:
                # Find the subscription and revert the user to the free plan
                user_subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
                user_subscription.plan = 'free'
                user_subscription.is_active = False
                user_subscription.save()
                print(f"Subscription cancelled for user {user_subscription.user.username}. Reverted to free plan.")
            except Subscription.DoesNotExist:
                pass # Subscription already deleted or not found

        return Response(status=status.HTTP_200_OK)