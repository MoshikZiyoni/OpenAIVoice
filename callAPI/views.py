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

import datetime
import os
import time
from urllib.parse import parse_qs
import django
import urllib

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OpenAIVoice.settings')
django.setup()
import json
import base64
import asyncio
from websockets.client import connect as ws_connect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from twilio.twiml.voice_response import VoiceResponse, Connect
from twilio.rest import Client
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Call
from asgiref.sync import sync_to_async
from django.core.cache import cache
from django.utils.timezone import now
import logging
logger = logging.getLogger(__name__)

TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER_NEW = os.getenv('TWILIO_PHONE_NUMBER_NEW')
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SYSTEM_MESSAGE = ("""
                  "Start the conversation by saying: 'הגעת לעסק של מושיק, במה אוכל לעזור?'"
                Speak in Hebrew with a warm, upbeat, and reassuring tone. Use a natural Israeli accent
               with clear, precise pronunciation. Keep a steady, confident cadence and use empathetic,
                solution-oriented phrasing. Focus on positive language and next steps.
                        """
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
    phone_number = request.POST.get('From')
    call_sid = request.POST.get('CallSid')
    if call_sid!=None and len(phone_number)>3:
        call, created = Call.objects.get_or_create(
        call_sid=call_sid,
        phone_number= phone_number,
        caller_id = TWILIO_PHONE_NUMBER_NEW,
        direction = "in"
    )
    
    logger.info(f"Call record {'created' if created else 'retrieved'}: {call}")
    cache_key = f"{call_sid}"
    cache._cache[cache_key] = call_sid
        
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
        """Accept the WebSocket connection."""
        logger.info("Client connected")
        await self.accept()
        self.call_sid = None
        self.call_start_time = time.time()
        try:
            # Iterate over all keys in the cache to find the one starting with "call_sid_"
            cache_data = cache._cache
            for key in cache_data.keys():
                logger.debug(f"Cache key: {key}")
                self.call_sid = key
                cache.clear()
        except Exception as e:
            logger.error(f"Error retrieving call_sid from cache: {e}")   
          
        
        if self.call_sid:
            logger.info(f"Retrieved call_sid from cache: {self.call_sid}")
        else:
            
            logger.warning("call_sid not found in cache, using default")
        # For websockets 15.0, we need to use "additional_headers"
        # But need to use the correct import and proper function
        
        
        self.openai_ws = await ws_connect(
            'wss://api.openai.com/v1/realtime?model=gpt-4o-mini-realtime-preview',
            extra_headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "OpenAI-Beta": "realtime=v1"
            }
        )
        
        # Initialize session with OpenAI
        await self.initialize_session()
        
        # Connection specific state
        self.stream_sid = None
        self.latest_media_timestamp = 0
        self.last_assistant_item = None
        self.mark_queue = []
        self.response_start_timestamp_twilio = None
        self.user_transcript_buffer = []  # Add this line
        self.current_transcription_id = None  # Add this line
        # Start background tasks
        self.receive_from_openai_task = asyncio.create_task(self.receive_from_openai())

    async def disconnect(self, close_code):
        """Handle disconnect."""
        logger.info(f"Client disconnected with code: {close_code}")
        call_duration = time.time() - self.call_start_time
        formatted_duration = round(call_duration, 2)  # Round to 2 decimal places
        logger.info(f"Call duration: {formatted_duration} seconds")
         # Update Call model with the calculated duration
        if self.call_sid:
            try:
                call = await sync_to_async(Call.objects.get)(call_sid=self.call_sid)
                call.total_duration = formatted_duration
                call.status = 'completed'
                for user_speech, ai_response in zip(
                    self.conversation_data["user_speech"], self.conversation_data["ai_responses"]
                ):
                    await sync_to_async(call.add_conversation_turn)(
                        text=user_speech,
                        is_ai=False,
                    )
                    await sync_to_async(call.add_conversation_turn)(
                        text=ai_response,
                        is_ai=True,
                    )
                await sync_to_async(call.save)()  # Save changes asynchronously
                
            except Exception as e:
                logger.error(f"Error updating call duration: {e}")
                
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
            # print(f"Incoming stream has started {self.stream_sid}")
            self.response_start_timestamp_twilio = None
            self.latest_media_timestamp = 0
            self.last_assistant_item = None
            
        elif data['event'] == 'mark':
            if self.mark_queue:
                self.mark_queue.pop(0)
                

    async def receive_from_openai(self):
        # Initialize a buffer to collect AI response text
        self.ai_response_text = ""
        self.conversation_data = {"user_speech": [], "ai_responses": []}
        try:
            async for openai_message in self.openai_ws:
                response = json.loads(openai_message)
                  # Add this to track all events
                # print("OpenAI Event:", response,'!!!')  # Add this to track all events

                # if response['type'] in LOG_EVENT_TYPES:
                #     print(f"Received event: {response['type']}", response)
                    
                if response.get('type') == 'conversation.item.input_audio_transcription.completed':
                    full_transcript = response.get('transcript', '').strip()
                    logger.info(f"USER FINAL SPEECH: {full_transcript}")
                    self.conversation_data["user_speech"].append(full_transcript)
                    # try:
                    #     # Use the saved call_sid instead of stream_sid
                    #     logger.debug(f"Call SID: {self.call_sid}")
                    #     call = await sync_to_async(Call.objects.get)(call_sid=self.call_sid)

                    #     # Add user message to conversation JSON field
                    #     await sync_to_async(call.add_conversation_turn)(
                    #         text=full_transcript,
                    #         is_ai=False,
                    #     )
                    # except Exception as e:
                    #     logger.error(f"Error saving user transcription: {e}")
                # If the response contains an audio delta and (optionally) text:
                if response.get('type') == 'response.audio.delta' and 'delta' in response:
                    # Process the audio as before...
                    # Optionally, if the API also returns text alongside audio:
                    delta_text = response.get('delta_text', '')
                    self.ai_response_text += delta_text

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

                    if response.get('item_id'):
                        self.last_assistant_item = response['item_id']

                    await self.send_mark()

                # Check for a signal that the AI has finished its response.
                if response.get('type') == 'response.done':
                    # Check if the response completed successfully.
                    if response.get('response', {}).get('status') == 'completed':
                        output_items = response['response'].get('output', [])
                        for item in output_items:
                            # Loop over the content list in the output item.
                            for content in item.get('content', []):
                                if content.get('type') == 'audio' and 'transcript' in content:
                                    ai_text = content['transcript']
                                    logger.info(f"AI final response: {ai_text}")
                                    self.conversation_data["ai_responses"].append(ai_text)
                                    # try:
                                    #     call = await sync_to_async(Call.objects.get)(call_sid=self.call_sid)
                                    #     await sync_to_async(call.add_conversation_turn)(
                                    #         text=ai_text,
                                    #         is_ai=True,
                                    #     )
                                    # except Exception as e:
                                    #     logger.error(f"Error saving AI response: {e}")
                    # Optionally reset the buffer if needed for the next response:
                    self.ai_response_text = ""

                if response.get('type') == 'input_audio_buffer.speech_started':
                    logger.info("Speech started detected.")
                    if self.last_assistant_item:
                        logger.info(f"Interrupting response with id: {self.last_assistant_item}")
                        await self.handle_speech_started_event()
                
        except Exception as e:
            logger.error(f"Error in receive_from_openai: {e}")


    async def handle_speech_started_event(self):
        """Handle interruption when the caller's speech starts."""
        logger.info("Handling speech started event.")
        if self.mark_queue and self.response_start_timestamp_twilio is not None:
            elapsed_time = self.latest_media_timestamp - self.response_start_timestamp_twilio
            if SHOW_TIMING_MATH:
                logger.debug(f"Calculating elapsed time for truncation: {self.latest_media_timestamp} - {self.response_start_timestamp_twilio} = {elapsed_time}ms")

            if self.last_assistant_item:
                if SHOW_TIMING_MATH:
                    logger.debug(f"Truncating item with ID: {self.last_assistant_item}, Truncated at: {elapsed_time}ms")

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
                 "input_audio_transcription": {
                "model": "gpt-4o-mini-transcribe",
                "language": "he",  # Language in ISO-639-1 format (Hebrew)
                "prompt": "Transcribe Hebrew speech accurately"  # Optional prompt for improved guidance
            }
            }
        }
        logger.info(f"Sending session update: {json.dumps(session_update)}")
        await self.openai_ws.send(json.dumps(session_update))

        # Uncomment the next line to have the AI speak first
        await self.send_initial_conversation_item()

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
                        "text": "start"
                        # "text":"Act as a professional phone operator, responding naturally and empathetically like a human. Handle calls with clarity, politeness, and adapt your tone based on the caller's emotions and needs."
                        # "text":"""
                        # "אתה עוזר קולי הפועל בשם ערן ציפל, מומחה לשיווק דיגיטלי. המטרה שלך היא לנהל שיחה אנושית, מקצועית וברורה, ולברר האם הפונה מעוניין באחד מהשירותים שערן מציע: אסטרטגיה שיווקית לעסקים ניהול תוכן לרשתות חברתיות סרטוני וידאו שיווקיים קמפיינים ממומנים עיצוב גרפי בניית אתרים ודפי נחיתה אוטומציות שיווק ודוא"ל כתיבת תוכן שיווקי הקשב ובדוק אם יש עניין בשירותים. אם יש עניין, שאל: מה התחום של העסק שלך? במה היית רוצה עזרה? האם עבדת בעבר עם משווק דיגיטלי? אם יש עניין ממשי, אמור: "מעולה, אני אעביר את זה לערן שיחזור אליך. רק אצטרך כמה פרטים:" שם מלא מספר טלפון נושא הפנייה הנחיה חשובה: אם הפונה שואל שאלה שאינה רלוונטית, השב: "אין לי תשובה לשאלה זו ואשמח להעביר את השאלה לערן שיחזור אליך עם תשובה בהקדם." אין להשתמש באימוג'ים או לבטא אותם בקול. הקפד לנהל שיחה אנושית, זורמת, ומתחשבת ככל האפשר."
                        # """
                    }
                ]
            }
        }
        await self.openai_ws.send(json.dumps(initial_conversation_item))
        await self.openai_ws.send(json.dumps({"type": "response.create"}))
        
        
        
@csrf_exempt
@require_http_methods(["POST"])
def make_outbound_call(request):
    
    """
    Handle outbound call requests. Expects a phone number in the request.
    Returns a JSON response with call status information.
    """
    try:
        # Parse the request body
        data = json.loads(request.body)
        to_number = data.get('phone_number')
        logger.info(f"Outbound call to number: {to_number}")
        if not to_number:
            return JsonResponse({"error": "Phone number is required"}, status=400)
        
        # Get host from request for webhook URL
        # host = request.get_host()
        # host = 'loves-crown-survey-ran.trycloudflare.com'
        host = 'web-production-7204.up.railway.app'
        # Create the TwiML for the outbound call
        response = VoiceResponse()
        connect = Connect()
        connect.stream(url=f'wss://{host}/media-stream')
        response.append(connect)
        # Make the outbound call
        call = twilio_client.calls.create(
            to=to_number,
            from_=TWILIO_PHONE_NUMBER_NEW,
            twiml=str(response),
            status_callback=f'https://{host}/call-status/',
            status_callback_event=['initiated', 'ringing', 'in-progress', 'completed'],
            status_callback_method='POST'
        )
        
        return JsonResponse({
            "success": True,
            "call_sid": call.sid,
            "status": call.status,
            "message": f"Call initiated to {to_number}"
        })
        
    except Exception as e:
        logger.error(f"Error making outbound call: {e}")
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def call_status_callback(request):
    """
    Handle Twilio call status callbacks.
    This endpoint will receive updates about the call status.
    """
    call_sid = request.POST.get('CallSid')
    call_status = request.POST.get('CallStatus')
    phone_number = request.POST.get("To")
    caller_id = request.POST.get("From")
    logger.info(f"Call status update received: {call_status} for CallSid: {call_sid}")

    if not call_sid:
        return JsonResponse({"error": "CallSid is required"}, status=400)
    
    if call_sid:
        call, created = Call.objects.get_or_create(
            call_sid=call_sid,
            defaults={
                "phone_number": phone_number,
                "caller_id": caller_id,
                "status": call_status,
                "direction": "out"
            }
        )
        if not created:
            # Update the existing record if needed
            call.status = call_status
            call.phone_number = phone_number
            call.caller_id = caller_id
            call.save()
        cache_key = f"{call_sid}"
        if cache_key not in cache._cache:
            cache._cache[cache_key] = call_sid
        # Log or store the call status as needed
        logger.info(f"Call {call_sid} status updated to: {call_status}")
    
    # You might want to store this in a database or trigger further actions
    
    return HttpResponse(status=200)

class OutboundMediaStreamConsumer(MediaStreamConsumer):
    """WebSocket consumer specifically for outbound calls."""
    
    async def connect(self):
        """Accept the WebSocket connection."""
        logger.info("Outbound call client connected")
        await super().connect()
        self.call_start_time = time.time()
    async def send_initial_conversation_item(self):
        """Send initial conversation item for outbound calls - typically a greeting."""
        initial_conversation_item = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text":"you are the master"
                        # "text": """
                        # "אתה עוזר קולי הפועל בשם ערן ציפל, מומחה לשיווק דיגיטלי. זוהי שיחת יוזמה שאנחנו מבצעים. 
                        # התחל בהצגה עצמית קצרה: 'שלום, מדבר ערן ציפל, מומחה לשיווק דיגיטלי. האם זה זמן נוח לשיחה קצרה?'
                        # אם הם אומרים שלא, הצע לחזור בזמן אחר ושאל מתי יהיה נוח. אם הם מסכימים לשוחח, הצג את השירותים שאתה מציע:
                        # אסטרטגיה שיווקית לעסקים
                        # ניהול תוכן לרשתות חברתיות
                        # סרטוני וידאו שיווקיים
                        # קמפיינים ממומנים
                        # עיצוב גרפי
                        # בניית אתרים ודפי נחיתה
                        # אוטומציות שיווק ודוא״ל
                        # כתיבת תוכן שיווקי
                        # אם יש עניין, שאל: מה התחום של העסק שלך? במה היית רוצה עזרה? האם עבדת בעבר עם משווק דיגיטלי?
                        # אם יש עניין ממשי, אמור: 'מעולה, אני רוצה לשמוע עוד על העסק שלך ואיך אני יכול לעזור. אצטרך כמה פרטים:' 
                        # שם מלא
                        # מספר טלפון להמשך שיחה
                        # דוא״ל
                        # תחום העסק ונושא הפנייה
                        # זמן מועדף לשיחת המשך מעמיקה יותר
                        # הנחיה חשובה: אם הפונה שואל שאלה שאינה רלוונטית, השב: 'אין לי תשובה מלאה לשאלה זו כרגע, אך אשמח לחזור אליך עם מידע מפורט בשיחה הבאה.'
                        # הקפד לנהל שיחה אנושית, זורמת, ומתחשבת ככל האפשר. בסיום השיחה, הודה להם על זמנם והדגש שתחזור אליהם בקרוב עם מידע נוסף."
                        # """
                    }
                ]
            }
        }
        await self.openai_ws.send(json.dumps(initial_conversation_item))
        await self.openai_ws.send(json.dumps({"type": "response.create"}))