
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# আপনার dream_analyzer.py ফাইল থেকে মূল ফাংশনটি ইম্পোর্ট করুন
from .dream_analyzer import merge_dream_interpretation

class DreamInterpretationAPIView(APIView):
   
    def post(self, request, *args, **kwargs):
        # রিকোয়েস্টের বডি থেকে 'query' ডেটা নিন
        user_query = request.data.get('query')

        if not user_query:
            return Response(
                {"error": "Please provide a dream query."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # আপনার অ্যানালাইজার ফাংশনটি কল করুন
            result = merge_dream_interpretation(user_query)
            
            # ফলাফলটিকে JSON হিসেবে ফেরত পাঠান
            return Response(result, status=status.HTTP_200_OK)
        
        except Exception as e:
            # অপ্রত্যাশিত কোনো এরর হলে
            return Response(
                {"error": f"An internal error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        


# new chatbot ************************************************ 
# api_app/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .dream import dream_chatbot_json # আপনার dream.py থেকে ফাংশনটি ইম্পোর্ট করুন

class DreamInterpretationView(APIView):
    """
    API view to interpret a dream query.
    Expects a POST request with a JSON body like: {"query": "dream description"}
    """
    def post(self, request, *args, **kwargs):
        # রিকোয়েস্টের বডি থেকে 'query' ডেটা নিন
        user_query = request.data.get('query')

        if not user_query:
            return Response(
                {"error": "Please provide a 'query' field with your dream description."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # আপনার ফাংশনটি কল করুন
        result = dream_chatbot_json(user_query)

        # যদি কোনো এরর হয়, তাহলে এরর রেসপন্স পাঠান
        if 'error' in result:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # সফল হলে, ফলাফলটি JSON হিসেবে ফেরত পাঠান
        return Response(result, status=status.HTTP_200_OK)