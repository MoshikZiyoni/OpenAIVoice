# import os
# import time
# import tempfile
# import openai
# from django.conf import settings
# from pydub import AudioSegment
# import requests

# class OpenAIService:
#     def __init__(self):
#         self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
#     def generate_speech(self, text, voice="alloy"):
#         """Generate speech from text using OpenAI's text-to-speech API"""
#         try:
#             temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
#             response = self.client.audio.speech.create(
#                 model="tts-1-hd",  # Using high-definition model for better quality
#                 voice=voice,
#                 input=text,
#                 speed=1.1  # Slightly faster speech for more natural conversation
#             )
#             response.stream_to_file(temp_file.name)
#             return temp_file.name
#         except Exception as e:
#             print(f"Error in generate_speech: {e}")
#             raise
    
#     def transcribe_audio(self, audio_url):
#         """Transcribe audio from URL using OpenAI's speech-to-text API"""
#         try:
#             # Download the audio file
#             temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
#             response = requests.get(audio_url)
#             with open(temp_file.name, 'wb') as f:
#                 f.write(response.content)
            
#             # Convert to MP3 if needed
#             if audio_url.endswith('.wav'):
#                 audio = AudioSegment.from_wav(temp_file.name)
#                 mp3_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
#                 audio.export(mp3_file.name, format="mp3")
#                 os.unlink(temp_file.name)
#                 temp_file = mp3_file
            
#             # Transcribe the audio
#             with open(temp_file.name, 'rb') as audio_file:
#                 transcription = self.client.audio.transcriptions.create(
#                     model="whisper-1",
#                     file=audio_file,
#                     language="en"
#                 )
            
#             os.unlink(temp_file.name)
#             return transcription.text
#         except Exception as e:
#             print(f"Error in transcribe_audio: {e}")
#             if os.path.exists(temp_file.name):
#                 os.unlink(temp_file.name)
#             return ""
    
#     def generate_response(self, prompt, conversation_history=None):
#         """Generate AI response based on prompt and conversation history"""
#         if conversation_history is None:
#             conversation_history = []
            
#         messages = [{"role": "system", "content": prompt}]
        
#         # Add conversation history
#         for turn in conversation_history:
#             role = "assistant" if turn.get('is_ai', True) else "user"
#             messages.append({"role": role, "content": turn.get('text', '')})
        
#         try:
#             response = self.client.chat.completions.create(
#                 model="gpt-4-turbo",
#                 messages=messages,
#                 temperature=0.7,
#                 max_tokens=150
#             )
#             return response.choices[0].message.content
#         except Exception as e:
#             print(f"Error in generate_response: {e}")
#             return "I'm sorry, I'm having trouble processing your request right now."