from rest_framework import serializers

class DreamInterpretationSerializer(serializers.Serializer):
    """
    API রিকোয়েস্টের বডি ভ্যালিডেট করার জন্য এই সিরিয়ালাইজার।
    """
    dream = serializers.CharField(max_length=5000, help_text="The user's dream description.")
    last_interpretation = serializers.CharField(required=False, allow_blank=True, help_text="The previous brief interpretation for a detailed follow-up.")
    detailed = serializers.BooleanField(default=False, help_text="Set to true for a more detailed explanation.")
    ask_sides = serializers.BooleanField(default=False, help_text="Set to true to ask for positive/negative sides.")