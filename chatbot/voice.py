# interpreter/services.py

import os
from openai import OpenAI
import whisper

# Initialize OpenAI client
# It is recommended to use environment variables for your API key
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "YOUR_DEFAULT_KEY"))

MODEL_ID = "gpt-4o-mini"

# Load Whisper model
whisper_model = whisper.load_model("base")

def audio_file_to_text(file_path: str, language: str = "en") -> str:
    """
    Converts an audio file into text using OpenAI Whisper.
    """
    if not os.path.exists(file_path):
        return "Error: File not found."

    result = whisper_model.transcribe(file_path, fp16=False, language=language)
    return result["text"]

def interpret_dream_openai(dream, detailed=False, ask_sides=False):
    # This function remains the same as in your original script
    if detailed:
        prompt = f"""
        You are a professional dream interpreter.
        The user had this dream: "{dream}".

        Your task:
        1. Give a clear and moderate explanation of the dream.
        2. Write it in a single paragraph.
        3. Naturally explain key elements inside the paragraph.
        4. Return the response strictly in JSON with only one key: "dreamExplanation".
        """
    else:
        if ask_sides:
            prompt = f"""
            The user had this dream: "{dream}".
            Please explain the dream in simple and clear words and provide moderate explanation.
            Also, describe the **positive sides** and the **negative sides / side effects** of this dream.
            Must return in JSON.
            """
        else:
            prompt = f"""
        You are a professional dream interpreter.
        The user had this dream: "{dream}".

        Your task:
        1. Give a clear and moderate explanation of the dream.
        2. Write it in a single paragraph.
        3. Naturally explain key elements inside the paragraph.
        4. Return the response strictly in JSON with only one key: "dreamExplanation".
        """

    response = client.chat.completions.create(
        model=MODEL_ID,
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.choices[0].message.content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json", "", 1).strip()

    return text