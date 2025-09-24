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