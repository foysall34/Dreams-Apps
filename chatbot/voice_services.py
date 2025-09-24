# services/voice_services.py

import os
import datetime
import requests
import whisper
from django.conf import settings

# A dictionary of available voices
VOICES = {
    "soothing_female": "pjcYQlDFKMbcOUp6F5GD",
    "deep_male": "kHhWB9Fw3aF6ly7JvltC",
    "calm_neutral": "ys3XeJJA4ArWMhRpcX1D"
}

def voice_to_text(audio_path: str):
    """
    Convert an audio file to text using OpenAI's Whisper model.
    
    Args:
        audio_path (str): The absolute path to the audio file.
        
    Returns:
        str: The transcribed text.
    """
    try:
        # Using a smaller model is faster; for higher accuracy, consider "base" or "medium"
        model = whisper.load_model("small")
        result = model.transcribe(audio_path)
        return result.get("text", "")
    except Exception as e:
        print(f"Error during voice-to-text transcription: {e}")
        return ""

def text_to_voice_elevenlabs(text: str, user_id: int, voice_choice: str = "soothing_female"):
    """
    Convert text to speech using the ElevenLabs API and save the file.
    
    Args:
        text (str): The text to convert to speech.
        user_id (int): The ID of the user to create a unique filename.
        voice_choice (str): The key for the desired voice from the VOICES dictionary.
        
    Returns:
        str: The URL path to the generated audio file, or None on failure.
    """
    api_key = settings.ELEVENLABS_API_KEY
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY is not set in Django settings.")

    voice_id = VOICES.get(voice_choice, VOICES["soothing_female"])
    api_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v1",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.7}
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=60) # Added timeout
        response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)

        # Create a unique filename and ensure the target directory exists
        timestamp = int(datetime.datetime.now().timestamp())
        relative_path = os.path.join('audio_files', f"dream_{user_id}_{timestamp}.mp3")
        absolute_path = os.path.join(settings.MEDIA_ROOT, relative_path)
        
        # Create the 'audio_files' directory inside MEDIA_ROOT if it doesn't exist
        os.makedirs(os.path.dirname(absolute_path), exist_ok=True)

        with open(absolute_path, "wb") as f:
            f.write(response.content)
            
        # Return the URL path, not the filesystem path
        return os.path.join(settings.MEDIA_URL, relative_path).replace("\\", "/")

    except requests.exceptions.RequestException as e:
        print(f"ElevenLabs API request failed: {e}")
        # Optionally, you can inspect response.text for more details if available
        # if e.response is not None:
        #     print(f"Response body: {e.response.text}")
        return None