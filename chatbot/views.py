
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.response import Response
from rest_framework import status
from .serializers import DreamInterpretationSerializer
from .deepseek_bot import interpret_dream_deepseek  


from .dream_analyzer import merge_dream_interpretation


class DreamInterpretationAPIView(APIView):
   
    def post(self, request, *args, **kwargs):
        user_query = request.data.get('query')
        if not user_query:
            return Response(
                {"error": "Please provide a dream query."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            result = merge_dream_interpretation(user_query)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"An internal error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        


# new chatbot ************************************************ 
# api_app/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .dream import dream_chatbot_json 

class DreamInterpretationView(APIView):
    """
    API view to interpret a dream query.
    Expects a POST request with a JSON body like: {"query": "dream description"}
    """
    def post(self, request, *args, **kwargs):
       
        user_query = request.data.get('query')

        if not user_query:
            return Response(
                {"error": "Please provide a 'query' field with your dream description."},
                status=status.HTTP_400_BAD_REQUEST
            )

      
        result = dream_chatbot_json(user_query)

        
        if 'error' in result:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(result, status=status.HTTP_200_OK)

# For deepSeek chatbot 

import json
from rest_framework.views import APIView


class DreamInterpretationAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = DreamInterpretationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)    
        validated_data = serializer.validated_data
        
        try:
            result_text = interpret_dream_deepseek(
                dream=validated_data.get('dream'),
                detailed=validated_data.get('detailed', False),
                last_interpretation=validated_data.get('last_interpretation'),
                ask_sides=validated_data.get('ask_sides', False)
            )
            cleaned_text = result_text.strip() 
            if cleaned_text.startswith("```json"):      
                cleaned_text = cleaned_text[7:-3].strip()
            elif cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:-3].strip()
            try:
                json_response = json.loads(cleaned_text)
 
                return Response(json_response, status=status.HTTP_200_OK)
            except json.JSONDecodeError:

                return Response({"interpretation": cleaned_text}, status=status.HTTP_200_OK)

        except ConnectionError as e:
            return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

# For voice api 
# interpreter/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, JSONParser
from .voice import audio_file_to_text, interpret_dream_openai
import os
from django.conf import settings
import json

class InterpretDreamView(APIView):
    parser_classes = [MultiPartParser, JSONParser]

    def post(self, request, *args, **kwargs):
        detailed = request.query_params.get('detailed', 'false').lower() == 'true'
        ask_sides = request.query_params.get('ask_sides', 'false').lower() == 'true'
        language = request.query_params.get('language', 'en')

        # Check if the request contains a file upload
        if 'voice' in request.FILES:
            voice_file = request.FILES['voice']
            
            # Save the uploaded file temporarily
            file_path = os.path.join(settings.MEDIA_ROOT, voice_file.name)
            with open(file_path, 'wb+') as destination:
                for chunk in voice_file.chunks():
                    destination.write(chunk)
            
            dream_text = audio_file_to_text(file_path, language=language)
            
            # Clean up the temporary file
            os.remove(file_path)

        # Check if the request contains JSON data
        elif 'dream' in request.data:
            dream_text = request.data.get('dream')
        
        else:
            return Response(
                {"error": "Please provide either a 'dream' in the request body or a 'voice' file."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not dream_text or dream_text.startswith("Error:"):
            return Response(
                {"error": "Could not process the provided input."},
                status=status.HTTP_400_BAD_REQUEST
            )

        interpretation = interpret_dream_openai(dream_text, detailed=detailed, ask_sides=ask_sides)
        
        try:
            # The OpenAI response is expected to be a JSON string
            return Response(json.loads(interpretation), status=status.HTTP_200_OK)
        except json.JSONDecodeError:
            return Response(
                {"error": "Failed to decode the interpretation from the external service."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )