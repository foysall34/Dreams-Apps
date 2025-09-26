

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Dream
from .serializers import DreamInterpretationSerializer , DreamHistorySerializer
from .import dream_interpreter, voice_services
from rest_framework import generics


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
        dream, created = Dream.objects.get_or_create(user=user, text=dream_text)

        if dream.status == 'completed':
            return Response(
                {"error": "Your limit finished for today"},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        if answers:
            if dream.status != 'initial' or not dream.interpretation:
                 return Response(
                    {"error": "Initial interpretation must be generated before submitting answers."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            ultimate_interpretation = dream_interpreter.generate_ultimate_interpretation(
                user.id, dream_text, answers
            )

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
                "audio_url": request.build_absolute_uri(audio_url)
            }
            return Response(response_data, status=status.HTTP_200_OK)

        if not created and dream.status == 'initial':
             return Response(
                {"error": "This dream has already been interpreted. Please provide answers to proceed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user_plan = validated_data['user_type']
        question_count = {'free': 2, 'premium': 5, 'platinum': 7}.get(user_plan, 2)

        interpretation, questions = dream_interpreter.generate_interpretation(
            user.id, dream_text, question_count
        )
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
            "audio_url": request.build_absolute_uri(audio_url),
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