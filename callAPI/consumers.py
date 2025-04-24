# # callAPI/consumers.py

# import os
# import json
# import asyncio
# import base64
# import tempfile
# from channels.generic.websocket import AsyncWebsocketConsumer
# import openai

# # Ensure your OpenAI API key is set (and Whisper access is enabled)
# OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
# openai.api_key = OPENAI_API_KEY

# class OpenAIVoiceConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         await self.accept()
#         # Initialize a buffer for accumulating audio chunks.
#         self.audio_buffer = []
#         # Start a background task to process audio every 10 seconds.
#         self.process_audio_task = asyncio.create_task(self.process_audio_loop())
    
#     async def disconnect(self, close_code):
#         if hasattr(self, 'process_audio_task'):
#             self.process_audio_task.cancel()
    
#     async def receive(self, text_data):
#         data = json.loads(text_data)
#         # Look for media events from Twilio.
#         if data.get("event") == "media":
#             payload = data.get("media", {}).get("payload")
#             if payload:
#                 self.audio_buffer.append(payload)
    
#     async def process_audio_loop(self):
#         """
#         Every 10 seconds, if audio has been buffered, write it to a temp file,
#         use OpenAI Whisper to transcribe it, and send the transcription.
#         """
#         while True:
#             await asyncio.sleep(10)  # Adjust the interval as needed.
#             if self.audio_buffer:
#                 # Combine the buffered base64 audio chunks.
#                 combined_audio = b"".join(
#                     [base64.b64decode(chunk) for chunk in self.audio_buffer]
#                 )
#                 self.audio_buffer = []  # Clear the buffer.
                
#                 # Write the combined audio to a temporary WAV file.
#                 with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
#                     tmp.write(combined_audio)
#                     temp_file_path = tmp.name
                
#                 # Run transcription in a thread to avoid blocking the event loop.
#                 loop = asyncio.get_event_loop()
#                 transcription = await loop.run_in_executor(None, transcribe_audio_file, temp_file_path)
#                 # Remove the temporary file.
#                 os.remove(temp_file_path)
                
#                 # If transcription was successful, send it back.
#                 if transcription:
#                     await self.send(text_data=json.dumps({"transcription": transcription}))

# def transcribe_audio_file(file_path):
#     """
#     Synchronously transcribe the audio file using OpenAI Whisper.
#     Returns the transcribed text or an empty string on error.
#     """
#     try:
#         with open(file_path, "rb") as audio_file:
#             result = openai.Audio.transcribe("whisper-1", audio_file)
#             return result.get("text", "")
#     except Exception as e:
#         print("Error in transcribe_audio_file:", e)
#         return ""
