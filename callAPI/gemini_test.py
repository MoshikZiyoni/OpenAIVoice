import json
import os
import time
from google.cloud import texttospeech
# # Configure Google Cloud Text-to-Speech client

from dotenv import load_dotenv
from django.conf import settings
###he-IL-Wavenet-B
# Set your OpenAI API key
settings.configure()
load_dotenv()
# ###he-IL-Wavenet-B # Removed comment about specific voice

# Import Google Cloud libraries
import google.generativeai as genai
from google.oauth2 import service_account

# Get the JSON string from the environment variable
service_account_info_str = os.getenv('GOOGLE_SERVICE_ACCOUNT_INFO')

if service_account_info_str:
    try:
        # Parse the JSON string into a dictionary
        service_account_info = json.loads(service_account_info_str)

        # Create credentials from the dictionary
        credentials = service_account.Credentials.from_service_account_info(service_account_info)

        # Initialize the TextToSpeechClient with the credentials
        tts_client = texttospeech.TextToSpeechClient(credentials=credentials)
    except Exception as e:
        print("Error creating credentials:", e)
        tts_client = None


# Configure Google Gemini API
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

# Choose the fastest Gemini model
gemini_model_name = "gemini-2.0-flash-lite"
gemini_model = genai.GenerativeModel(gemini_model_name)

"""
Function to generate the Gemini response and TTS audio.
This runs in a background thread.
"""
try:
    # Start timing for text generation
    start_time = time.time()

    # Generate AI response using Gemini (text)
    response = gemini_model.generate_content(
        "מה המצב אח שלי?",
        generation_config=genai.types.GenerationConfig(
            temperature=0.7,
            max_output_tokens=100
        )
    )
    ai_response = response.text.strip()
    print("Generated ai_response:", ai_response)
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Time taken for Gemini response: {total_time:.2f} seconds")
except Exception as e:
    print("Error with Gemini response:", e)
    ai_response = "מצטער איני יכול לעזור כרגע"

# Save the AI response.
# ConversationTurn.objects.create(call=call_obj, text=ai_response, is_ai=True)

# Start timing for TTS generation
start_time = time.time()
try:
    # Convert the AI response to audio using Google Cloud Text-to-Speech.
    synthesis_input = texttospeech.SynthesisInput(text=ai_response)

    # Choose a fast Standard voice for Hebrew (you might need to explore other Standard voices)
    voice = texttospeech.VoiceSelectionParams(
        language_code="he-IL",
        ssml_gender = texttospeech.SsmlVoiceGender.NEUTRAL,  # Male or Female voice.
        name="he-IL-standard-B"  # This is a fast Standard voice. Explore others like A, C, D.
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = tts_client.synthesize_speech(
        request={"input": synthesis_input, "voice": voice, "audio_config": audio_config}
    )

    audio_filename = f"tts_test1.mp3"
    audio_filepath = os.path.join(settings.MEDIA_ROOT, audio_filename)
    with open(audio_filepath, "wb") as out:
        out.write(response.audio_content)
        print("TTS audio generated at:", audio_filepath)

except Exception as e:
    print("TTS error:", e)

# End timing
end_time = time.time()
total_time = end_time - start_time
print(f"Time taken for Google TTS generation: {total_time:.2f} seconds")