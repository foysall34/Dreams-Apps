# api_app/dream.py

import google.generativeai as genai
import re
import json
from django.conf import settings # Django সেটিংস ইম্পোর্ট করুন

# Configure Gemini API using the key from settings.py
try:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    MODEL_ID = "gemini-1.5-flash"  # অথবা আপনার পছন্দের মডেল
    model = genai.GenerativeModel(MODEL_ID)
    print("Gemini model configured successfully.")
except AttributeError:
    print("Error: GEMINI_API_KEY not found in settings. Please configure it.")
    model = None

def dream_chatbot_json(user_query):
    if not model:
        return {"error": "Gemini model is not configured. Check your API key."}

    prompt = f"""
    You are a dream interpreter.
    Give a moderate and simple explanation of the dream in easy words.
    Avoid difficult terms and keep it straightforward.
    Also provide a short 2–3 line summary.
    Answer strictly in JSON format without markdown or extra text.

    Dream: "{user_query}"

    JSON format:
    {{
        "interpretation": "easy explanation here",
        "summary": "short summary here"
    }}
    """
    try:
        response = model.generate_content(prompt)
        raw_text = response.text.strip()

        # Remove markdown code fences if Gemini adds them
        raw_text = re.sub(r"^```[a-zA-Z]*", "", raw_text).strip()
        raw_text = re.sub(r"```$", "", raw_text).strip()

        result = json.loads(raw_text)
        return result

    except Exception as e:
        # Gemini থেকে কোনো কারণে এরর আসলে বা JSON পার্স না হলে
        return {"error": f"Failed to get or parse response: {str(e)}", "raw": raw_text if 'raw_text' in locals() else "No response text."}