# # Download the helper library from https://www.twilio.com/docs/python/install
import os
from twilio.rest import Client

# # Set environment variables for your credentials
# # Read more at http://twil.io/secure




# import base64
# import os
# from openai import OpenAI
# from twilio.rest import Client
# import openai
# from django.conf import settings
# from pathlib import Path

# BASE_DIR = Path(__file__).resolve().parent.parent

# # client = OpenAI.api_key = (OpenAI_API_KEY)
# # Initialize Twilio client

# try:
#     tts_completion = openai.audio.speech.create(
#         model="gpt-4o-mini-tts",
#         voice="alloy",
#         input="מה המצב?"
#     )
#     # Print the text part of the response for debugging
#     tts_completion.stream_to_file("output.wav")
#     # Decode the base64 audio data to bytes
#     wav_data_b64 = tts_completion.choices[0].message.audio.data
#     wav_bytes = base64.b64decode(wav_data_b64)
    
#     # Save the WAV file in your media folder.
#     audio_filename = f"tts_test.wav"
#     with open("hebrew_output.wav", "wb") as f:
#         f.write(wav_bytes)
    
#     # Construct the URL to serve the audio file.
#     # Ensure settings.MEDIA_URL is correctly configured and publicly accessible.
    
# except Exception as e:
#     print("TTS error:", e)
#     audio_url = None

# import os
# import requests

# # File path
# audio_url = r"C:\Users\MoshikZiyoni\OpenAIVoice\media\tts_20.wav"
# audio_filepath = audio_url  # Use the absolute path directly

# if not os.path.exists(audio_filepath):
#     print(f"File not found: {audio_filepath}")
# else:
#     try:
#         upload_url = "https://api.anonfiles.com/upload"  # AnonFiles upload URL

#         # Use 'with' to ensure the file is properly closed
#         with open(audio_filepath, 'rb') as f:
#             files = {'file': f}
#             response = requests.post(upload_url, files=files,verify=False,cert=False)

#         # Check the response status code
#         if response.status_code == 200:
#             response_json = response.json()
#             if response_json.get('status'):
#                 public_url = response_json['data']['file']['url']['full']
#                 print("Public URL:", public_url)
#             else:
#                 print(f"Error uploading to AnonFiles: {response_json}")
#         else:
#             print(f"Error uploading to AnonFiles. Status code: {response.status_code}, Response: {response.text}")
#     except Exception as e:
#         print(f"An error occurred during file upload to AnonFiles: {e}")