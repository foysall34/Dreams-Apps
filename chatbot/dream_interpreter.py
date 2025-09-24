# services/dream_interpreter.py

from openai import OpenAI
from django.conf import settings
from .models import Dream # Assuming your Dream model is in the 'services' app or accessible

# Initialize the OpenAI client for DeepSeek
# It's best practice to check if the key exists
if not settings.OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in Django settings.")

client = OpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url="https://api.deepseek.com"
)

def generate_interpretation(user, dream_text, question_count):
    """
    Generates the initial dream interpretation and follow-up questions.
    
    Args:
        user (User): The Django user instance.
        dream_text (str): The text of the dream to interpret.
        question_count (int): The number of follow-up questions to generate.
    
    Returns:
        tuple: A tuple containing the interpretation (str) and questions (str).
    """
    # Fetch previous dreams for context from the database
    previous_dreams = Dream.objects.filter(user=user).order_by('-created_at')[:5] # Get last 5 dreams
    
    context_text = ""
    if previous_dreams:
        context_text = "For context, here are the user's previous dreams and interpretations:\n"
        for dream in previous_dreams:
            if dream.interpretation: # Only include dreams that have been interpreted
                context_text += f"- Dream: {dream.text}\n  Interpretation: {dream.interpretation}\n"

    system_prompt = f"""
You are a professional Dream Interpreter Chatbot. Analyze dreams with empathy and symbolic depth in 4–5 lines.
Ask exactly {question_count} follow-up questions connected to dream colors, symbols, emotions, people (friends, family, strangers),
and whether the user was an observer or participant.
{context_text}
"""
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": dream_text}
            ],
            temperature=0.7
        )
        output_text = response.choices[0].message.content.strip()
        lines = output_text.split("\n")

        # A more robust way to separate interpretation from questions
        interpretation_lines = []
        question_lines = []
        for line in lines:
            # Simple heuristic: lines starting with a number or question mark are questions
            if line.strip().startswith(('?', '1', '2', '3', '4', '5', '6', '7')):
                question_lines.append(line)
            else:
                interpretation_lines.append(line)

        interpretation = "\n".join(interpretation_lines).strip()
        questions = "\n".join(question_lines).strip()

        # Fallback if splitting fails to find questions
        if not questions and len(lines) > question_count:
            interpretation = "\n".join(lines[:-question_count]).strip()
            questions = "\n".join(lines[-question_count:]).strip()

        return interpretation, questions

    except Exception as e:
        # It's good practice to handle potential API errors
        print(f"Error calling DeepSeek API: {e}")
        return "Sorry, I was unable to process the interpretation at this moment.", ""


def generate_ultimate_interpretation(dream_text, original_questions, user_answers):
    """
    Generates the final, detailed interpretation based on user's answers.

    Args:
        dream_text (str): The original dream text.
        original_questions (str): The questions that were asked to the user.
        user_answers (str): The user's answers to the questions.

    Returns:
        str: The ultimate interpretation text.
    """
    prompt = f"""
You are an expert Dream Interpreter Chatbot. Your task is to provide a final, conclusive interpretation within (5-6 lines).
The user originally dreamed about: "{dream_text}"
You followed up by asking: "{original_questions}"
The user has now provided their answers: "{user_answers}"

Based on their answers, synthesize all the information to provide a detailed, insightful, and ultimate interpretation of their dream. Connect the symbols, emotions, and their personal feedback into a coherent narrative.
"""
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        ultimate_interpretation = response.choices[0].message.content.strip()
        return ultimate_interpretation
    except Exception as e:
        print(f"Error calling DeepSeek API for ultimate interpretation: {e}")
        return "Sorry, I was unable to generate the final interpretation at this moment."