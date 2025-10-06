

import os
import datetime
import requests
import whisper
from django.conf import settings

# A dictionary of available voices
VOICES = {

    "Soothing_female": "pjcYQlDFKMbcOUp6F5GD",
    "Deep_male": "kHhWB9Fw3aF6ly7JvltC",
    "Calm_neutral": "ys3XeJJA4ArWMhRpcX1D" ,
    "Michael": "uju3wxzG5OhpWcoi3SMy",
    "cera": "ucgJ8SdlW1CZr9MIm8BP",
    "clara": "8LVfoRdkh4zgjr8v5ObE",
    "Christopher": "1YGgSmpRGVzkcaI7zhbX",
    "Eve": "G4Wh6MqJNTzYtuAeMqv5",
    "John": "c4NIULtANlpduSDihsKJ",
    "David": "iEw1wkYocsNy7I7pteSN",

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

def text_to_voice_elevenlabs(text: str, user_id: int, voice_choice: str = "Soothing_female"):
    api_key = settings.ELEVENLABS_API_KEY
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY is not set in Django settings.")

    voice_id = VOICES.get(voice_choice, VOICES["Soothing_female"])
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

    print("DEBUG → API_URL:", api_url)
    print("DEBUG → API_KEY:", api_key[:5] + "****")

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error: {http_err} → {response.text}")
        return None
    except Exception as e:
        print(f"Request failed: {e}")
        return None

    timestamp = int(datetime.datetime.now().timestamp())
    relative_path = os.path.join('audio_files', f"dream_{user_id}_{timestamp}.mp3")
    absolute_path = os.path.join(settings.MEDIA_ROOT, relative_path)
    os.makedirs(os.path.dirname(absolute_path), exist_ok=True)

    with open(absolute_path, "wb") as f:
        f.write(response.content)

    return os.path.join(settings.MEDIA_URL, relative_path).replace("\\", "/")
