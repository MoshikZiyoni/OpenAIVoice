# callAPI/views.py

import datetime
import os
import time
from urllib.parse import parse_qs
import django
import urllib

# from callAPI.summary import handle_summary

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
from django.db.models import Count, Avg, F, Q,Sum
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from rest_framework.response import Response

import logging
logger = logging.getLogger(__name__)

TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER_NEW = os.getenv('TWILIO_PHONE_NUMBER_NEW')
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SYSTEM_MESSAGE = ("""
                Speak in Hebrew with a warm, upbeat, and reassuring tone. Use a natural Israeli accent
               with clear, precise pronunciation. Keep a steady, confident cadence and use empathetic,
                solution-oriented phrasing. Focus on positive language and next steps.
                        "אתה עוזר קולי הפועל בשם ערן, מומחה לשיווק דיגיטלי. זוהי שיחת יוזמה שאנחנו מבצעים. 
                        התחל בהצגה עצמית קצרה: 'שלום, מדבר הסוכן של ערן, מומחה לשיווק דיגיטלי. האם זה זמן נוח לשיחה קצרה?'
                        אם הם אומרים שלא, הצע לחזור בזמן אחר ושאל מתי יהיה נוח. אם הם מסכימים לשוחח, הצג את השירותים שאתה מציע:
                        אסטרטגיה שיווקית לעסקים
                        ניהול תוכן לרשתות חברתיות
                        סרטוני וידאו שיווקיים
                        קמפיינים ממומנים
                        עיצוב גרפי
                        בניית אתרים ודפי נחיתה
                        אוטומציות שיווק ואימייל
                        כתיבת תוכן שיווקי
                        אם יש עניין, שאל: מה התחום של העסק שלך? במה היית רוצה עזרה? האם עבדת בעבר עם משווק דיגיטלי?
                        אם יש עניין ממשי, אמור: 'מעולה, אני רוצה לשמוע עוד על העסק שלך ואיך אני יכול לעזור. אצטרך כמה פרטים:' 
                        שם מלא
                        מספר טלפון להמשך שיחה
                        אימייל
                        תחום העסק ונושא הפנייה
                        זמן מועדף לשיחת המשך מעמיקה יותר
                        הנחיה חשובה: אם הפונה שואל שאלה שאינה רלוונטית, השב: 'אין לי תשובה מלאה לשאלה זו כרגע, אך אשמח לחזור אליך עם מידע מפורט בשיחה הבאה.'
                        הקפד לנהל שיחה אנושית, זורמת, ומתחשבת ככל האפשר. בסיום השיחה, הודה להם על זמנם והדגש שתחזור אליהם בקרוב עם מידע נוסף."
                        
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
        
        # if self.call_sid:
        #     handle_summary(self.call_sid)
            
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
                # "model": "gpt-4o-mini-transcribe",
                "model": "whisper-1",
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
        host = 'fitting-hazardous-accordance-weather.trycloudflare.com'
        # host = 'web-production-7204.up.railway.app'
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
        
        
        
        
@require_http_methods(["GET"])
def get_calls(request):
    """
    Get a paginated list of calls with optional filtering.
    """
    # Get query parameters for filtering
    direction = request.GET.get('direction', '')
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')
    page = request.GET.get('page', 1)
    limit = request.GET.get('limit', 10)
    
    # Start with all calls
    calls_query = Call.objects.all()
    
    # Apply filters if provided
    if direction:
        calls_query = calls_query.filter(direction=direction)
    if status:
        calls_query = calls_query.filter(status=status)
    if search:
        calls_query = calls_query.filter(
            Q(phone_number__contains=search) | 
            Q(caller_id__contains=search)
        )
    
    # Order by most recent first
    calls_query = calls_query.order_by('-created_at')
    
    # Paginate results
    paginator = Paginator(calls_query, limit)
    try:
        calls_page = paginator.page(page)
    except PageNotAnInteger:
        calls_page = paginator.page(1)
    except EmptyPage:
        calls_page = paginator.page(paginator.num_pages)
    
    # Format response
    calls_data = []
    for call in calls_page:
        calls_data.append({
            'id': call.id,
            'phone_number': call.phone_number,
            'caller_id': call.caller_id,
            'status': call.status,
            'direction': call.direction,
            'total_duration': call.total_duration,
            'call_sid': call.call_sid,
            'formatted_created_at': call.formatted_created_at(),
            'formatted_updated_at': call.formatted_updated_at(),
        })
    
    return JsonResponse({
        'results': calls_data,
        'count': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': int(page)
    })

@require_http_methods(["GET"])
def get_call_detail(request, call_id):
    """
    Get detailed information about a specific call.
    """
    try:
        call = Call.objects.get(id=call_id)
        
        call_data = {
            'id': call.id,
            'phone_number': call.phone_number,
            'caller_id': call.caller_id,
            'status': call.status,
            'direction': call.direction,
            'total_duration': call.total_duration,
            'call_sid': call.call_sid,
            'formatted_created_at': call.formatted_created_at(),
            'formatted_updated_at': call.formatted_updated_at(),
            'conversation': call.conversation,
        }
        
        return JsonResponse(call_data)
    except Call.DoesNotExist:
        return JsonResponse({'error': 'Call not found'}, status=404)

@require_http_methods(["GET"])
def get_call_stats(request):
    """
    Get statistics about the calls.
    """
    stats = {
        'totalCalls': Call.objects.count(),
        'incomingCalls': Call.objects.filter(direction='in').count(),
        'outgoingCalls': Call.objects.filter(direction='out').count(),
        'completedCalls': Call.objects.filter(status='completed').count(),
        'failedCalls': Call.objects.filter(status='failed').count(),
        'inProgressCalls': Call.objects.filter(status='in_progress').count(),
        'averageDuration': Call.objects.aggregate(avg_duration=Avg('total_duration'))['avg_duration'] or 0,
        'totalDuration': Call.objects.aggregate(total_duration=Sum('total_duration'))['total_duration'] or 0,

    }
    
    return JsonResponse(stats)

@csrf_exempt
@require_http_methods(["POST"])
def initiate_outbound_call(request):
    """
    Initiate an outbound call from the React frontend.
    This is a wrapper around the existing make_outbound_call function but with
    authentication and additional validation.
    """
    # The authentication would typically be handled by Auth0
    # in the frontend, so here we just need to validate the request
    
    try:
        data = json.loads(request.body)
        
        # Basic validation
        if not data.get('phone_number'):
            return JsonResponse({'error': 'Phone number is required'}, status=400)
        
        # Call the existing function to make the outbound call
        return make_outbound_call(request)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)