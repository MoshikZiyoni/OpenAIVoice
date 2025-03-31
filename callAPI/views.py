# # callAPI/views.py

# import base64
# import json
# import os
# import random
# import time
# import concurrent
# from django.shortcuts import get_object_or_404
# from django.http import HttpResponse, JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from django.conf import settings
# import requests
# from twilio.rest import Client
# from twilio.twiml.voice_response import VoiceResponse, Gather,Stream
# from .models import Call, ConversationTurn
# from rest_framework.decorators import api_view
# import openai
# from dotenv import load_dotenv
# import threading
# import google.generativeai as genai
# from google.cloud import texttospeech
# # # Configure Google Cloud Text-to-Speech client
# from google.oauth2 import service_account

# audio_generation_complete = threading.Event()


# # Get the JSON string from the environment variable
# service_account_info_str = os.getenv('GOOGLE_SERVICE_ACCOUNT_INFO')

# if service_account_info_str:
#     try:
#         # Parse the JSON string into a dictionary
#         service_account_info = json.loads(service_account_info_str)

#         # Create credentials from the dictionary
#         credentials = service_account.Credentials.from_service_account_info(service_account_info)

#         # Initialize the TextToSpeechClient with the credentials
#         tts_client = texttospeech.TextToSpeechClient(credentials=credentials)
#     except Exception as e:
#         print("Error creating credentials:", e)
#         tts_client = None

# # Configure Google Gemini API
# GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
# genai.configure(api_key=GOOGLE_API_KEY)
# load_dotenv()

# # Set your OpenAI API key
# OPENAI_API_KEY= settings.OPENAI_API_KEY
# openai.api_key = OPENAI_API_KEY
# # Initialize Twilio client
# twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


# @csrf_exempt
# @api_view(['POST'])
# def make_call(request):
#     """
#     Initiate an outbound call by creating a Call object and using Twilio's API.
#     """
#     if request.method == 'POST':
#         phone_number = request.data.get('phone_number')
#         print("phone_number", phone_number)
#         TWILIO_PHONE_NUMBER_NEW = os.getenv('TWILIO_PHONE_NUMBER_NEW')
#         print(TWILIO_PHONE_NUMBER_NEW)
#         print(type(TWILIO_PHONE_NUMBER_NEW))
#         if not phone_number:
#             return JsonResponse({'error': 'Phone number required'}, status=400)
        
#         # Create a new call record
#         call_obj = Call.objects.create(
#             phone_number=phone_number,
#             caller_id=settings.TWILIO_PHONE_NUMBER_NEW
#         )
#         print("New call obg creadted")
#         # Use PUBLIC_URL from environment for a publicly accessible callback URL.
#         public_url = "https://workforce-wines-independently-whether.trycloudflare.com/"
#         # public_url = "https://web-production-7204.up.railway.app"
#         if public_url:
#             callback_url = f'{public_url}/api/call/{call_obj.id}/twiml/'
#             status_callback_url = f'{public_url}/api/call/{call_obj.id}/status/'
#         else:
#             # Fallback: This will work only if your server is publicly accessible.
#             callback_url = request.build_absolute_uri(f'/api/call/{call_obj.id}/twiml/')
#             status_callback_url = request.build_absolute_uri(f'/api/call/{call_obj.id}/status/')
#         print("Start calling")
#         if not os.path.exists(settings.MEDIA_ROOT):
#             os.makedirs(settings.MEDIA_ROOT, exist_ok=True)  # Safe creation

#         # try:
#         #     tts_completion = openai.audio.speech.create(
#         #         model="gpt-4o-mini-tts",
#         #         voice="alloy",  # Optionally remove if you prefer the default voice.
#         #         instructions=(
#         #             "Speak in Hebrew with a warm, upbeat, and reassuring tone. Use a natural Israeli accent "
#         #             "with clear, precise pronunciation. Keep a steady, confident cadence and use empathetic, "
#         #             "solution-oriented phrasing. Focus on positive language and next steps."
#         #         ),
#         #         input="היי אני העוזר הוירטואלי של מושיק"
#         #     )
#         #     welcome_audio_filename = f"tts'_welcome_{call_obj.id}.mp3"
#         #     audio_filepath = os.path.join(settings.MEDIA_ROOT, welcome_audio_filename)
#         #     tts_completion.stream_to_file(audio_filepath)
            
#         # except Exception as e:
#         #     print("TTS error:", e)
#         import shutil

#         # Ensure ummm.wav exists in MEDIA_ROOT
#         umm_filepath = os.path.join(settings.MEDIA_ROOT, "ummm.wav")
#         if not os.path.exists(umm_filepath):
#             source_path = os.path.join(os.path.dirname(__file__), "static", "ummm.wav")  # Adjust source path
#             shutil.copy(source_path, umm_filepath)
            
#         haha_filepath = os.path.join(settings.MEDIA_ROOT, "haha.wav")
#         if not os.path.exists(haha_filepath):
#             source_path = os.path.join(os.path.dirname(__file__), "static", "haha.wav")  # Adjust source path
#             shutil.copy(source_path, haha_filepath)

#         # Ensure Hey.wav exists in MEDIA_ROOT
#         hey_filepath = os.path.join(settings.MEDIA_ROOT, "Hey.wav")
#         if not os.path.exists(hey_filepath):
#             source_path = os.path.join(os.path.dirname(__file__), "static", "Hey.wav")  # Adjust source path
#             shutil.copy(source_path, hey_filepath)
#         try:
#             umm_filepath = os.path.join(settings.MEDIA_ROOT, "ummm.wav")
#             if os.path.exists(umm_filepath):
#                 print(f"File exists at: {umm_filepath}")
#             else:
#                 print("File not found!")
#         except Exception as e:
#             print("Error in ummm.wav file:", e)
        
#         try:
#             haha_filepath = os.path.join(settings.MEDIA_ROOT, "haha.wav")
#             if os.path.exists(haha_filepath):
#                 print(f"File exists at: {haha_filepath}")
#             else:
#                 print("File not found!")
#         except Exception as e:
#             print("Error in haha.wav file:", e)
            
#         try:
#             hey_filepath = os.path.join(settings.MEDIA_ROOT, "Hey.wav")
#             if os.path.exists(hey_filepath):
#                 print(f"File exists at: {hey_filepath}")
#             else:
#                 print("File not found!")
#         except Exception as e:
#             print("Error in Hey.wav file:", e)
       
#         if os.path.exists(settings.MEDIA_ROOT):
#             print("Files in MEDIA_ROOT:")
#             for file_name in os.listdir(settings.MEDIA_ROOT):
#                 print(file_name)
#         else:
#             print("MEDIA_ROOT directory does not exist:", settings.MEDIA_ROOT)
        
#         # Initiate the outbound call using Twilio
#         try:
            
#             twilio_call = twilio_client.calls.create(
#                 to=phone_number,
#                 from_=TWILIO_PHONE_NUMBER_NEW,
#                 url=callback_url,
#                 status_callback=status_callback_url,
#                 status_callback_event=['completed', 'failed']
#             )
#         except Exception as e:
#             return JsonResponse({'error': str(e)}, status=500)
        
#         # Save the Twilio Call SID
#         call_obj.call_sid = twilio_call.sid
#         call_obj.save()
        
#         return JsonResponse({'message': 'Call initiated', 'call_id': call_obj.id})
#     else:
#         return JsonResponse({'error': 'POST request required'}, status=400)


# @csrf_exempt
# def call_twiml(request, call_id):
#     """
#     Generate TwiML for the ongoing call.
#     Immediately play a filler ("ummm…") and concurrently start generating the GPT response.
#     Then, redirect to the play_response endpoint to play the generated GPT answer audio.
#     """
#     public_url = "https://workforce-wines-independently-whether.trycloudflare.com/"
#     # public_url = "https://web-production-7204.up.railway.app"
#     call_obj = get_object_or_404(Call, id=call_id)
#     response = VoiceResponse()
    
#     speech_result = request.POST.get('SpeechResult') or request.GET.get('SpeechResult')
#     # partial_speech = request.POST.get('PartialSpeechResult') or request.GET.get('PartialSpeechResult')
    
#     # if partial_speech:
#     #     print("Partial speech received:", partial_speech)
    
#     if speech_result:
#         print("User said:", speech_result)
#         ConversationTurn.objects.create(call=call_obj, text=speech_result, is_ai=False)
        
#         # Build conversation history.
#         # conversation = [{
#         #     "role": "system",
#         #     "content": (
#         #         "Well, you're an AI assistant that speaks regular Hebrew, like, in a totally chill way "
#         #         "and with good vibes. Throw in some Israeli slang (like 'sababa') and keep a good atmosphere, bro."
#         #     )
#         # }]
#         # for turn in call_obj.conversation.all():
#         #     role = "assistant" if turn.is_ai else "user"
#         #     conversation.append({"role": role, "content": turn.text})
#         conversation= []
#         conversation.append({
#             "role": "user",  
#             "parts": [{"text": (
#                 "You're a phone call agent that speaks regular Hebrew in a friendly and professional tone. "
#                 "Maintain a calm and helpful demeanor, and use common Israeli slang (like 'sababa') where appropriate to keep the conversation approachable and positive. "
#                 "Avoid using emojis in your responses."
#             )}]
#         })
#         for turn in call_obj.conversation.all():
#             role = "model" if turn.is_ai else "user"  # Gemini uses "model" for AI
#             conversation.append({"role": role, "parts": [{"text": turn.text}]})
        
        
        
        
#         # Immediately play the filler audio.
#         try:
#             filler_choices = ["ummm.wav", "haha.wav"]
#             chosen_filler = random.choice(filler_choices)
#             filler_url = f"{public_url}/media/{chosen_filler}"
#             print("Playing filler audio:", filler_url)
#             response.play(filler_url)
#         except Exception as e:
#             print("Filler audio error:", e)
#             response.say("ummm...")
#         # Start background thread to generate GPT response and TTS audio.
#         with concurrent.futures.ThreadPoolExecutor() as executor:
#             future = executor.submit(generate_gpt_audio, call_obj, conversation, speech_result)
#             gemini_text = future.result()
#             response.say(voice="Google.he-IL-Standard-B",message=gemini_text)
#             gather = Gather(
#             speechModel="default",
#             input='speech',
#             language='he-IL',
#             action=request.build_absolute_uri(),
#             timeout=1,
#             speechTimeout=1,
#             hints="שלום, מה המצב, הלו, היי"
#         )
#         response.append(gather)
#         # timeout = 10  # Maximum wait time in seconds
#         # if audio_generation_complete.wait(timeout):
#         #     audio_filename = f"tts_{call_obj.id}.mp3"
#         #     try:
#         #         audio_url = f"{public_url}/media/{audio_filename}"
#         #         print("Playing generated audio:", audio_url)
#         #         response.play(audio_url)
#         #     except Exception as e:
#         #         print("Error playing audio:", e)
#         #         response.say("מצטער, אירעה שגיאה בהשמעת התגובה.", language="he-IL")
    
#     else:
#         # response.pause(length=1)
#         try:
#             welcome_filename = "Hey.wav"
#             welcome_url = f"{public_url}/media/{welcome_filename}"
#             print("Playing welcome audio:", welcome_url)
#             response.play(welcome_url)
#         except Exception as e:
#             print("Welcome audio error:", e)
#             response.say("Hi")
    
#     # Set up a <Gather> element for continuous speech capture.
#     gather = Gather(
#         speechModel="default",
#         input='speech',
#         language='he-IL',
#         action=request.build_absolute_uri(),
#         timeout=1,
#         speechTimeout=1,
#         hints="שלום, מה המצב, הלו, היי"
#     )
#     response.append(gather)
#     response.redirect(request.build_absolute_uri())
    
#     return HttpResponse(response.to_xml(), content_type='application/xml')
# def generate_gpt_audio(call_obj, conversation,speech_result):
#     # """
#     # Function to generate the GPT response and TTS audio.
#     # This runs in a background thread.
#     # """
#     # try:
#     #     # Start timing
#     #     start_time = time.time()

#     #     # Generate AI response using ChatCompletion (text)
#     #     completion = openai.chat.completions.create(
#     #         model="gpt-4o-mini",
#     #         messages=conversation,
#     #         temperature=0.7,
#     #         max_tokens=100
#     #     )
#     #     ai_response = completion.choices[0].message.content.strip()
#     #     print("Generated ai_response:", ai_response)
#     # except Exception as e:
#     #     print("Error with GPT response:", e)
#     #     ai_response = "מצטער איני יכול לעזור כרגע"
    
#     gemini_model_name = "gemini-2.0-flash-lite"
#     generation_config = {
#                 "temperature": 1,
#                 "top_p": 1,
#                 "top_k": 1,
#                 "max_output_tokens": 2048,
#             }
#     gemini_model = genai.GenerativeModel(gemini_model_name,
#                                          generation_config=generation_config)

#     """
#     Function to generate the Gemini response and TTS audio.
#     This runs in a background thread.
#     """
#     try:
#         # Start timing for text generation
#         start_time = time.time()
#         print("last converstion: ",conversation)
#         # Generate AI response using Gemini (text)
#         convo = gemini_model.start_chat(
#             history=conversation,  
#         )
#         convo.send_message(speech_result)
        
#         ai_response = convo.last.text.strip()
#         print("Generated ai_response:", ai_response)
#         end_time = time.time()
#         total_time = end_time - start_time
#         print(f"Time taken for Gemini response: {total_time:.2f} seconds")
#     except Exception as e:
#         print("Error with Gemini response:", e)
#         ai_response = "מצטער איני יכול לעזור כרגע"
    
    
#     # Save the AI response.
#     ConversationTurn.objects.create(call=call_obj, text=ai_response, is_ai=True)
#     return ai_response
#     # start_time = time.time()
    
#     # try:
#     #     # Convert the AI response to audio using Google Cloud Text-to-Speech.
#     #     synthesis_input = texttospeech.SynthesisInput(text=ai_response)

#     #     # Choose a fast Standard voice for Hebrew (you might need to explore other Standard voices)
#     #     voice = texttospeech.VoiceSelectionParams(
#     #         language_code="he-IL",
#     #         ssml_gender = texttospeech.SsmlVoiceGender.NEUTRAL,  # Male or Female voice.
#     #         name="he-IL-standard-B"  # This is a fast Standard voice. Explore others like A, C, D.
#     #     )

#     #     audio_config = texttospeech.AudioConfig(
#     #         audio_encoding=texttospeech.AudioEncoding.MP3
#     #     )

#     #     response = tts_client.synthesize_speech(
#     #         request={"input": synthesis_input, "voice": voice, "audio_config": audio_config}
#     #     )

#     #     audio_filename = f"tts_{call_obj.id}.mp3"
#     #     audio_filepath = os.path.join(settings.MEDIA_ROOT, audio_filename)
#     #     with open(audio_filepath, "wb") as out:
#     #         out.write(response.audio_content)
#     #         print("TTS audio generated at:", audio_filepath)
#         # audio_generation_complete.set()
#     # except Exception as e:
#     #     audio_generation_complete.set()
#     #     print("TTS error:", e)

#     # End timing
#     end_time = time.time()
#     total_time = end_time - start_time
#     print(f"Time taken for Google TTS generation: {total_time:.2f} seconds")
#     # start_time = time.time()
#     # try:
#     #     # Convert the AI response to audio using GPT-4o-Audio-Preview.
#     #     tts_completion = openai.audio.speech.create(
#     #         model="gpt-4o-mini-tts",
#     #         voice="alloy",
#     #         instructions=(
#     #             "Speak in Hebrew with a warm, upbeat, and reassuring tone. Use a natural Israeli accent "
#     #             "with clear, precise pronunciation. Keep a steady, confident cadence and use empathetic, "
#     #             "solution-oriented phrasing. Focus on positive language and next steps."
#     #         ),
#     #         input=ai_response
#     #     )
#     #     audio_filename = f"tts_{call_obj.id}.mp3"
#     #     audio_filepath = os.path.join(settings.MEDIA_ROOT, audio_filename)
#     #     tts_completion.stream_to_file(audio_filepath)
#     #     print("TTS audio generated at:", audio_filepath)
#     # except Exception as e:
#     #     print("TTS error:", e)

#     # # End timing
#     # end_time = time.time()
#     # total_time = end_time - start_time
#     # print(f"Time taken for GPT response and TTS generation: {total_time:.2f} seconds")
        


# @csrf_exempt
# @api_view(['POST'])
# def call_status(request, call_id):
#     """
#     Handle call status updates from Twilio.
#     """
#     call_obj = get_object_or_404(Call, id=call_id)
#     call_status = request.POST.get('CallStatus')
#     if call_status:
#         call_obj.status = call_status
#         call_obj.save()
#     return HttpResponse("Status updated")


# def get_calls(request):
#     """
#     API endpoint to list all calls.
#     """
#     calls = Call.objects.all().values()
#     return JsonResponse(list(calls), safe=False)


# def get_conversation(request, call_id):
#     """
#     API endpoint to retrieve the conversation for a specific call.
#     """
#     call_obj = get_object_or_404(Call, id=call_id)
#     conversation = list(call_obj.conversation.all().values())
#     return JsonResponse(conversation, safe=False)



# @csrf_exempt
# def partial_callback(request):
#     """Handle partial speech results from Twilio."""
#     print("Request POST data: %s", request.POST)
#     partial_speech = request.POST.get('PartialSpeechResult')
#     if partial_speech:
#         print("Partial speech detected:", partial_speech)
#         # Optionally: Process partial text here (e.g., send to OpenAI early)
#     return HttpResponse(status=200)  # Empty response (TwiML not required)


# @csrf_exempt
# def incoming_call(request):
#     """
#     Handle an incoming call by:
#     1. Greeting the caller.
#     2. Using Twilio's Gather to collect user input (speech or DTMF).
#     3. Streaming call audio to a WebSocket endpoint for real-time transcription using OpenAI Whisper.
#     4. Keeping the call open with a pause.
#     """
#     public_url = "https://guided-sun-individual-sentence.trycloudflare.com"
#     response = VoiceResponse()

#     # Greet the caller.
#     response.say("Welcome, please wait while we connect you to our AI assistant.")
#     response.pause(length=1)

#     # Use Gather to collect user input.
#     gather = response.gather(
#         input="speech dtmf",
#         action=f"{public_url}/process_input",  # Callback URL to process user input.
#         method="POST",
#         timeout=5,
#         num_digits=1
#     )
#     gather.say("Please say something or press a key to continue.")

#     # Stream the audio to the WebSocket endpoint where your AI processing occurs.
#     stream_url = f"wss://guided-sun-individual-sentence.trycloudflare.com/wss/openai_voice/"
#     stream = Stream(url=stream_url)
#     response.append(stream)

#     # Add a long pause to keep the call active while processing happens.
#     response.pause(length=60)

#     # Prepend the XML header required by Twilio.
#     twiml_response = '<?xml version="1.0" encoding="UTF-8"?>' + str(response)
#     return HttpResponse(twiml_response, content_type="application/xml")












# callAPI/views.py
import os
import json
import base64
import asyncio
import websockets
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from twilio.twiml.voice_response import VoiceResponse, Connect, Say, Stream
from channels.generic.websocket import AsyncWebsocketConsumer

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SYSTEM_MESSAGE = (
                "Speak in Hebrew with a warm, upbeat, and reassuring tone. Use a natural Israeli accent "
                "with clear, precise pronunciation. Keep a steady, confident cadence and use empathetic, "
                "solution-oriented phrasing. Focus on positive language and next steps."
)
VOICE = 'alloy'
LOG_EVENT_TYPES = [
    'error', 'response.content.done', 'rate_limits.updated',
    'response.done', 'input_audio_buffer.committed',
    'input_audio_buffer.speech_stopped', 'input_audio_buffer.speech_started',
    'session.created'
]
SHOW_TIMING_MATH = False

if not OPENAI_API_KEY:
    raise ValueError('Missing the OpenAI API key. Please set it in your Django settings or environment variables.')

def index_page(request):
    """Simple index endpoint to check if server is running."""
    return JsonResponse({"message": "Twilio Media Stream Server is running!"})

@csrf_exempt
@require_http_methods(["GET", "POST"])
def handle_incoming_call(request):
    """Handle incoming call and return TwiML response to connect to Media Stream."""
    response = VoiceResponse()
    # <Say> punctuation to improve text-to-speech flow
    # response.say("HEY")
    # response.pause(length=1)
    # response.say("start")
    
    # Get host from request
    host = request.get_host()
    
    connect = Connect()
    connect.stream(url=f'wss://{host}/media-stream')
    response.append(connect)
    
    return HttpResponse(str(response), content_type="application/xml")

class MediaStreamConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer to handle the media stream between Twilio and OpenAI."""
    
    async def connect(self):
        try:
            print("Client connected")
            await self.accept()
            
            # Add more detailed logging
            print("Attempting to connect to OpenAI WebSocket...")
            
            # Your existing connection code...
            
            print("Connected to OpenAI WebSocket successfully")
            # Rest of your code...
            
        except Exception as e:
            import traceback
            print(f"Error connecting to WebSocket: {e}")
            print(traceback.format_exc())
            # Make sure to still accept the connection even if OpenAI connection fails
            if not self.accepted:
                await self.accept()
                await self.close(code=1011)  # Internal server error code

    async def disconnect(self, close_code):
        """Handle disconnect."""
        print(f"Client disconnected with code: {close_code}")
        if hasattr(self, 'openai_ws') and self.openai_ws.open:
            await self.openai_ws.close()
        
        if hasattr(self, 'receive_from_openai_task'):
            self.receive_from_openai_task.cancel()
            
    async def receive(self, text_data):
        """Handle incoming messages from Twilio."""
        data = json.loads(text_data)
        
        if data['event'] == 'media' and self.openai_ws.open:
            self.latest_media_timestamp = int(data['media']['timestamp'])
            audio_append = {
                "type": "input_audio_buffer.append",
                "audio": data['media']['payload']
            }
            await self.openai_ws.send(json.dumps(audio_append))
            
        elif data['event'] == 'start':
            self.stream_sid = data['start']['streamSid']
            print(f"Incoming stream has started {self.stream_sid}")
            self.response_start_timestamp_twilio = None
            self.latest_media_timestamp = 0
            self.last_assistant_item = None
            
        elif data['event'] == 'mark':
            if self.mark_queue:
                self.mark_queue.pop(0)

    async def receive_from_openai(self):
        """Receive events from the OpenAI Realtime API, send audio back to Twilio."""
        try:
            async for openai_message in self.openai_ws:
                response = json.loads(openai_message)
                if response['type'] in LOG_EVENT_TYPES:
                    print(f"Received event: {response['type']}", response)

                if response.get('type') == 'response.audio.delta' and 'delta' in response:
                    audio_payload = base64.b64encode(base64.b64decode(response['delta'])).decode('utf-8')
                    audio_delta = {
                        "event": "media",
                        "streamSid": self.stream_sid,
                        "media": {
                            "payload": audio_payload
                        }
                    }
                    await self.send(text_data=json.dumps(audio_delta))

                    if self.response_start_timestamp_twilio is None:
                        self.response_start_timestamp_twilio = self.latest_media_timestamp
                        if SHOW_TIMING_MATH:
                            print(f"Setting start timestamp for new response: {self.response_start_timestamp_twilio}ms")

                    # Update last_assistant_item safely
                    if response.get('item_id'):
                        self.last_assistant_item = response['item_id']

                    await self.send_mark()

                # Trigger an interruption. Your use case might work better using `input_audio_buffer.speech_stopped`, or combining the two.
                if response.get('type') == 'input_audio_buffer.speech_started':
                    print("Speech started detected.")
                    if self.last_assistant_item:
                        print(f"Interrupting response with id: {self.last_assistant_item}")
                        await self.handle_speech_started_event()
        except Exception as e:
            print(f"Error in receive_from_openai: {e}")

    async def handle_speech_started_event(self):
        """Handle interruption when the caller's speech starts."""
        print("Handling speech started event.")
        if self.mark_queue and self.response_start_timestamp_twilio is not None:
            elapsed_time = self.latest_media_timestamp - self.response_start_timestamp_twilio
            if SHOW_TIMING_MATH:
                print(f"Calculating elapsed time for truncation: {self.latest_media_timestamp} - {self.response_start_timestamp_twilio} = {elapsed_time}ms")

            if self.last_assistant_item:
                if SHOW_TIMING_MATH:
                    print(f"Truncating item with ID: {self.last_assistant_item}, Truncated at: {elapsed_time}ms")

                truncate_event = {
                    "type": "conversation.item.truncate",
                    "item_id": self.last_assistant_item,
                    "content_index": 0,
                    "audio_end_ms": elapsed_time
                }
                await self.openai_ws.send(json.dumps(truncate_event))

            await self.send(text_data=json.dumps({
                "event": "clear",
                "streamSid": self.stream_sid
            }))

            self.mark_queue.clear()
            self.last_assistant_item = None
            self.response_start_timestamp_twilio = None

    async def send_mark(self):
        """Send mark event to Twilio."""
        if self.stream_sid:
            mark_event = {
                "event": "mark",
                "streamSid": self.stream_sid,
                "mark": {"name": "responsePart"}
            }
            await self.send(text_data=json.dumps(mark_event))
            self.mark_queue.append('responsePart')

    async def initialize_session(self):
        """Control initial session with OpenAI."""
        session_update = {
            "type": "session.update",
            "session": {
                "turn_detection": {"type": "server_vad"},
                "input_audio_format": "g711_ulaw",
                "output_audio_format": "g711_ulaw",
                "voice": VOICE,
                "instructions": SYSTEM_MESSAGE,
                "modalities": ["text", "audio"],
                "temperature": 0.8,
            }
        }
        print('Sending session update:', json.dumps(session_update))
        await self.openai_ws.send(json.dumps(session_update))

        # Uncomment the next line to have the AI speak first
        # await self.send_initial_conversation_item()

    async def send_initial_conversation_item(self):
        """Send initial conversation item if AI talks first."""
        initial_conversation_item = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "ברך את המשתמש במילים 'שלום! אני עוזר קולי המופעל על ידי Twilio ו-OpenAI Realtime API. אתה יכול לשאול אותי על עובדות, בדיחות או כל דבר שתוכל לדמיין. איך אוכל לעזור לך?'"
                    }
                ]
            }
        }
        await self.openai_ws.send(json.dumps(initial_conversation_item))
        await self.openai_ws.send(json.dumps({"type": "response.create"}))