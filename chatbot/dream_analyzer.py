# chatbot/dream_analyzer.py

import json
import requests
import google.generativeai as genai
from django.conf import settings

# API Key গুলো settings.py থেকে লোড হবে
genai.configure(api_key=settings.GOOGLE_API_KEY)

# পরিবর্তনটি এখানে করা হয়েছে: একটি স্থিতিশীল মডেল আইডি ব্যবহার করা হয়েছে
MODEL_ID = "gemini-1.5-flash"

def interpret_dream_gemini(user_query):
    """
    Sends the dream query to Gemini model and returns interpretation.
    """
    try:
        model = genai.GenerativeModel(MODEL_ID)
        response = model.generate_content(
            f"You are an expert dream interpreter. Explain the meaning of this dream in a shorter way:\n{user_query}"
        )
        return response.text.strip()
    except Exception as e:
        return f"Error communicating with Gemini: {e}"


def get_web_insights_serper(user_query, top_k=3):
    """
    Uses Serper API to get top-k related snippets for the dream query.
    """
    try:
        url = "https://google.serper.dev/search"
        headers = {"X-API-KEY": settings.SERPER_API_KEY, "Content-Type": "application/json"}
        payload = {"q": f"{user_query} dream meaning"}
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        results = data.get("organic", [])
        snippets = [item.get("snippet", "No snippet available.") for item in results[:top_k]]

        if not snippets:
            return ["No web insights found."]
        return snippets

    except requests.exceptions.RequestException as e:
        return [f"Error fetching web insights: {e}"]
    except Exception as e:
        return [f"An unexpected error occurred with Serper: {e}"]


def merge_dream_interpretation(user_query):
    """
    Generates structured dictionary output combining Gemini interpretation and web insights.
    """
    llm_response = interpret_dream_gemini(user_query)
    web_snippets = get_web_insights_serper(user_query)

    ultimate_interpretation = f"{llm_response} Merged with key themes from web insights and make it short: {'; '.join(web_snippets)}"

    output_data = {
        "dream_query": user_query,
        "ai_interpretation": llm_response,
        "web_insights": web_snippets,
        "ultimate_interpretation": ultimate_interpretation,
    }
    
    return output_data