pip install -U openai-whisper openai elevenlabs

import datetime
import requests
import whisper
import os
from openai import OpenAI


# DeepSeek API (uses OpenAI-compatible client)
os.environ["OPENAI_API_KEY"] = "open ai key"
client = OpenAI(base_url="https://api.deepseek.com")   # <-- DeepSeek endpoint

ELEVENLABS_API_KEY = "Your elevenlabs key "
DEFAULT_MODEL = "eleven_multilingual_v1"


# ====================== SESSION MEMORY ======================
user_sessions = {}

def get_user_context(user_id: str):
    return user_sessions.get(user_id, {"dreams": []})

def update_user_context(user_id: str, dream_text=None, interpretation=None,
                        questions=None, answers=None, ultimate=None):
    if user_id not in user_sessions:
        user_sessions[user_id] = {"dreams": []}

    if answers and ultimate:
        if user_sessions[user_id]["dreams"]:
            user_sessions[user_id]["dreams"][-1]["answers"] = answers
            user_sessions[user_id]["dreams"][-1]["ultimate"] = ultimate
    else:
        user_sessions[user_id]["dreams"].append({
            "dream_text": dream_text,
            "interpretation": interpretation,
            "questions": questions,
            "answers": None,
            "ultimate": None
        })


# ====================== VOICE FUNCTIONS ======================
VOICES = {
    "soothing_female": "pjcYQlDFKMbcOUp6F5GD",
    "deep_male": "kHhWB9Fw3aF6ly7JvltC",
    "calm_neutral": "ys3XeJJA4ArWMhRpcX1D"
}

def voice_to_text(audio_path: str):
    """Convert voice to text using Whisper."""
    model = whisper.load_model("small")
    result = model.transcribe(audio_path)
    return result["text"]

def text_to_voice_elevenlabs(
    text: str,
    user_id: str,
    voice_choice: str = "soothing_female",
    api_key: str = ELEVENLABS_API_KEY,
    model: str = DEFAULT_MODEL
):
    voice_id = VOICES.get(voice_choice, VOICES["soothing_female"])

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "model": model,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.7}
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        filename = f"dream_{user_id}_{voice_choice}_{int(datetime.datetime.now().timestamp())}.mp3"
        with open(filename, "wb") as f:
            f.write(response.content)
        return filename
    else:
        raise Exception(f"ElevenLabs TTS API failed: {response.status_code}, {response.text}")


# ====================== CORE DREAM FUNCTIONS ======================
def generate_interpretation(user_id, dream_text, question_count):
    prev_context = get_user_context(user_id)
    context_text = ""
    if prev_context["dreams"]:
        context_text = "Here are previous dreams and interpretations:\n"
        for d in prev_context["dreams"]:
            context_text += f"- Dream: {d['dream_text']}\n  Interpretation: {d['interpretation']}\n"

    system_prompt = f"""
You are a professional Dream Interpreter Chatbot. Analyze dreams with empathy and symbolic depth in 4–5 lines.
Ask exactly {question_count} follow-up questions connected to dream colors, symbols, emotions, people (friends, family, strangers),
and whether the user was an observer or participant.
{context_text}
"""
    response = client.chat.completions.create(
        model="deepseek-chat",   # DeepSeek model
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": dream_text}
        ],
        temperature=0.7
    )
    output_text = response.choices[0].message.content.strip()
    lines = output_text.split("\n")

    interpretation = "\n".join(lines[:-question_count]).strip()
    questions = "\n".join(lines[-question_count:]).strip()

    update_user_context(user_id, dream_text, interpretation, questions)

    return interpretation, questions

def generate_ultimate_interpretation(user_id, answers):
    context = get_user_context(user_id)
    if not context["dreams"]:
        return "No previous dream found."

    last_dream = context["dreams"][-1]
    dream_text = last_dream["dream_text"]
    questions = last_dream["questions"]

    prompt = f"""
You are a Dream Interpreter Chatbot.
User previously dreamed: "{dream_text}"
You asked: "{questions}"
User's answers: "{answers}"
Provide a concise ultimate interpretation (max 4–5 sentences),
focusing on the key emotional or symbolic meaning
"""
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role":"user","content":prompt}],
        temperature=0.7
    )
    ultimate = response.choices[0].message.content.strip()

    update_user_context(user_id, answers=answers, ultimate=ultimate)
    return ultimate


# ====================== TIER FUNCTIONS ======================
def free_plan(user_id, dream_text=None, answers=None, stage="initial"):
    if stage == "initial":
        interpretation, questions = generate_interpretation(user_id, dream_text, question_count=2)
        return {"interpretation": interpretation, "questions": questions}
    elif stage == "followup":
        ultimate = generate_ultimate_interpretation(user_id, answers)
        return {"ultimate_interpretation": ultimate}

def premium_plan(user_id, dream_text=None, audio_path=None, answers=None, stage="initial"):
    if stage == "initial":
        if audio_path:
            dream_text = voice_to_text(audio_path)
        interpretation, questions = generate_interpretation(user_id, dream_text, question_count=5)
        return {"interpretation": interpretation, "questions": questions}
    elif stage == "followup":
        ultimate = generate_ultimate_interpretation(user_id, answers)
        return {"ultimate_interpretation": ultimate}

def platinum_plan(user_id, dream_text=None, audio_path=None, answers=None,
                  stage="initial", voice_choice="soothing_female"):

    if stage == "initial":
        if audio_path:
            dream_text = voice_to_text(audio_path)
        interpretation, questions = generate_interpretation(user_id, dream_text, question_count=7)
        full_text = f"{interpretation}\nFollow-up Questions:\n{questions}"
        audio_file = text_to_voice_elevenlabs(full_text, user_id, voice_choice=voice_choice)
        return {"interpretation": interpretation, "questions": questions, "audio_file": audio_file}

    elif stage == "followup":
        ultimate = generate_ultimate_interpretation(user_id, answers)
        audio_file = text_to_voice_elevenlabs(ultimate, user_id, voice_choice=voice_choice)
        return {"ultimate_interpretation": ultimate, "audio_file": audio_file}


from IPython.display import Audio, display
from google.colab import files

def realtime_chat_platinum(user_id):
    print("🌙 Welcome to Dream Interpreter (Platinum Plan)!")
    stage = "initial"

    while True:
        if stage == "initial":
            inp = input("\n💭 Describe your dream (type 'voice' to upload audio, or type your dream, 'exit' to quit): ")
            if inp.lower() == "exit":
                print("Goodbye! Sweet dreams 🌙")
                break

            # Voice input
            if inp.lower() == "voice":
                print("Please upload your audio file (.mp3 or .wav)")
                uploaded = files.upload()
                audio_path = list(uploaded.keys())[0]
                print("Transcribing audio...")
                dream_text = voice_to_text(audio_path)
                print(f"\n📝 Transcribed Dream:\n{dream_text}")
            else:
                dream_text = inp

            # Ask user for voice choice
            print("\n🎙️ Choose a voice:")
            print("1. Soothing Female")
            print("2. Deep Male")
            print("3. Calm Neutral")
            choice = input("Enter number (1/2/3): ").strip()
            if choice == "2":
                voice_choice = "deep_male"
            elif choice == "3":
                voice_choice = "calm_neutral"
            else:
                voice_choice = "soothing_female"

            # Generate interpretation + 7 follow-up questions
            res = platinum_plan(user_id, dream_text=dream_text, stage="initial", voice_choice=voice_choice)
            print(f"\n📝 Interpretation:\n{res['interpretation']}")
            print(f"\n❓ Follow-up Questions:\n{res['questions']}")

            # Play TTS audio for interpretation + questions
            display(Audio(res['audio_file'], autoplay=True))

            stage = "followup"
            selected_voice = voice_choice  # store for follow-up

        elif stage == "followup":
            answers = input("\n✏️ Answer the follow-up questions (or type 'exit'): ")
            if answers.lower() == "exit":
                print("Goodbye! Sweet dreams 🌙")
                break

            # Ultimate interpretation + TTS
            res = platinum_plan(user_id, answers=answers, stage="followup", voice_choice=selected_voice)
            print(f"\n💡 Ultimate Interpretation:\n{res['ultimate_interpretation']}")
            display(Audio(res['audio_file'], autoplay=True))

            stage = "initial"

realtime_chat_platinum(user_id="user001")


