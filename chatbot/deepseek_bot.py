# dream_interpreter/services.py

import openai
import json
from django.conf import settings  # Django settings ইম্পোর্ট করুন

# ক্লায়েন্টকে এখানে কনফিগার করুন
try:
    client = openai.OpenAI(
        api_key=settings.DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com"
    )
    MODEL_ID = "deepseek-chat"
except Exception as e:
    # যদি API কী সেট করা না থাকে তবে হ্যান্ডেল করার জন্য
    client = None
    print(f"Warning: DeepSeek client could not be initialized. Error: {e}")


def interpret_dream_deepseek(dream, detailed=False, last_interpretation=None, ask_sides=False):
    if not client:
        raise ConnectionError("DeepSeek API client is not configured. Please check your API key.")

    # আপনার প্রম্পট তৈরির লজিক একই থাকবে
    if detailed:
        prompt = f"""
        The user shared this dream: "{dream}".
        The previous short interpretation was: "{last_interpretation}".
        Please explain this dream in more detail, in easy words.
        Just explain the meaning of the dream clearly with JSON.
        """
    elif ask_sides:
        prompt = f"""
        The user had this dream: "{dream}".
        Please explain the dream in simple and clear words.
        Also, describe the **positive sides** and the **negative sides / side effects** of this dream.
        must return in JSON.
        """
    else:
        prompt = f"""
        The user had this dream: "{dream}".
        Please explain the dream in simple and clear words.
        must return in JSON.
        """

    response = client.chat.completions.create(
        model=MODEL_ID,
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.choices[0].message.content.strip()
    return text