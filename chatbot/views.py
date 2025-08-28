
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