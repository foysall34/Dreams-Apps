# dreams/serializers.py

from rest_framework import serializers
from .models import Dream 

class DreamInterpretationSerializer(serializers.ModelSerializer):
    # 'answers' is write-only, it's for input on the 2nd request
    answers = serializers.ListField(
        child=serializers.CharField(), write_only=True, required=False
    )
    user_type = serializers.ChoiceField(
        choices=['free', 'premium', 'platinum'], write_only=True
    )
    # audio_url is read-only, it's for output
    audio_url = serializers.CharField(read_only=True, required=False)
    ans_type = serializers.CharField(read_only=True, required=False)


    class Meta:
        model = Dream
        fields = [
            'id', 'text', 'user_type', 'interpretation', 'questions',
            'answers', 'ultimate_interpretation', 'audio_url', 'ans_type'
        ]
        read_only_fields = ['id', 'interpretation', 'questions', 'ultimate_interpretation']



from rest_framework import serializers

class AudioGenerationSerializer(serializers.Serializer):
    """
    Serializer for the audio generation endpoint.
    Validates the text, user_type, and voice_type.
    """
    text = serializers.CharField()
    user_type = serializers.ChoiceField(choices=['free', 'premium', 'platinum'])
    voice_type = serializers.CharField(required=False, default='soothing_female')

    def validate_text(self, value):
        """
        Check that the text is not empty.
        """
        if not value.strip():
            raise serializers.ValidationError("Text cannot be empty.")
        return value



class DreamHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Dream
        fields = (
            'id', 
            'text', 
            'interpretation', 
            'questions', 
            'answers', 
            'ultimate_interpretation', 
            'status', 
            'created_at'
        )

# your_app_name/serializers.py

from rest_framework import serializers
from .models import Pricing

class PricingSerializer(serializers.ModelSerializer):

    features = serializers.SerializerMethodField()

    class Meta:
        model = Pricing
      
        fields = ['id', 'billing_interval', 'description', 'price', 'features']

    def get_features(self, obj):
    
        return obj.get_features()
    


# chatbot/serializers.py
from rest_framework import serializers
from .models import Pricing

class PricingMinimalSerializer(serializers.ModelSerializer):
    features = serializers.SerializerMethodField()

    class Meta:
        model = Pricing
        fields = ['id', 'plan_type', 'stripe_price_id', 'price', 'billing_interval' , 'features']

    def get_features(self, obj):
        return [feature['name'] for feature in obj.get_features()]
