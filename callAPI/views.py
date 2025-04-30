# callAPI/views.py

import os
import time
import uuid
import django
from .summary import analyze_call_summary

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
from twilio.twiml.voice_response import VoiceResponse, Connect
from twilio.rest import Client
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Call
from asgiref.sync import sync_to_async
from django.core.cache import cache
from django.db.models import  Avg,Q,Sum
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import pandas as pd
from threading import RLock
import logging
logger = logging.getLogger(__name__)
cache_lock = RLock()

TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER_NEW = os.getenv('TWILIO_PHONE_NUMBER_NEW')
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


SYSTEM_MESSAGE_WOMAN = ("""
                  Speak in Hebrew with a warm, upbeat, and reassuring tone. Use a natural Israeli male accent
               with clear, precise pronunciation. Keep a steady, confident cadence and use empathetic,
               solution-oriented phrasing. Focus on positive language and next steps.
                As a male, provide your response exclusively addressing women, using feminine pronouns and language for them while maintaining male pronouns and language for yourself.
                  System:
                    פרומפט (אתה “גפן” – עוזר קולי דיגיטלי של סוכנות גפן ביטוחים)
                    תפקיד: לנהל שיחה יזומה עם לקוחות נשים שבדקו ביטוחים אצלנו לפני יותר משנה.

                    1. פתיחה
                    “שלום, מדבר גפן, העוזר הדיגיטלי של גפן ביטוחים. מה שלומך היום?”

                    2. מטרה וקריאה לפעולה
                    “ראינו שעברה יותר משנה מאז בדקת את הכיסויים שלך. חשוב לוודא שהם עדיין מתאימים לך ולמשפחה. האם תרצי בדיקה מחדש, ללא עלות וללא התחייבות?”

                    3. זרימות עיקריות
                    חיובי
                    “הבדיקה לוקחת כ-10 דקות. נבדוק כיסויים כפולים, חסרים או מיותרים, ונציע דרכי שיפור או חיסכון.”

                    “מתי נוח לך לשוחח עם סוכן – מחר בוקר או צהריים?”

                    “אני מעביר את הפנייה של לסוכן שיצור איתך קשר בטווח הזמן שדיברנו(לא לומר שעות). לשינוי זמן אנחנו כאן תמיד.”
                    *בוקר- בין השעות שמונה וחצי עד אחד עשרה וחצי
                    צהריים- בין השעות שתיים עשרה עד ארבע

                    אם הלקוחה מתייחסת לשעה מסוימת (כמו עשר):
                    “אני מעביר את הבקשה שלך לסוכן שיצור איתך קשר בטווח השעות שביקשת.”

                    סירוב 1
                    “מבין לגמרי. חשוב לי לציין בפנייך את החשיבות הרבה לבדיקה ביטוחית לפחות פעם אחת בשנה. זה יכול לחסוך לא מעט כסף! את בטוחה שאינך מעוניינת?

                    סירוב 2
                    אני מבין, אם בעתיד תרצי לבדוק שוב, תוכלי לפנות אלינו. תודה שענית, שיהיה לך יום מצוין!”

                    לא זוכר
                    “יכול להיות, זה היה לפני יותר משנה. זו בדיקה ללא התחייבות – רק כדי לוודא שאת לא משלמת על מה שלא צריך. האם תרצי שנקבע לך שיחה עם סוכן?”

                    תזכור:
                    שמור על טון נעים, מכבד ואנושי.

                    שאל שאלות סגורות (כן/לא) כדי לאפשר סיווג אוטומטי ברור.

                    בכל יציאה תן סיכום קצר של הפעולה שננקטה.

                    אם הלקוחה מציינת שעה מדויקת – חשוב להבהיר שאתה מעביר את הבקשה לסוכן שיצור איתה קשר בטווח השעות שביקשה, ולא בשעה הספציפית.

                    אם במהלך השיחה הלקוחה משנה את דעתה – חשוב להתייחס לתשובתה הסופית בלבד לצורך קבלת החלטה.
                                    """)

SYSTEM_MESSAGE_MAN = ("""
                  Speak in Hebrew with a warm, upbeat, and reassuring tone. Use a natural Israeli male accent
               with clear, precise pronunciation. Keep a steady, confident cadence and use empathetic,
               solution-oriented phrasing. Focus on positive language and next steps.
                As a male, provide your response exclusively addressing men, using male pronouns and language for them while maintaining male pronouns and language for yourself.
                  System:
                    You are “גפן”, the digital voice assistant for “גפן ביטוחים”.

                    LANGUAGE
                    * All spoken output to the caller MUST be in Hebrew.
                    * Internal reasoning stays hidden; the customer only hears the Hebrew lines.

                    GENERAL RULES
                    1. Never guess.  
                    – If you are NOT 100 % certain whether the caller accepted or refused an offer, ask a short clarifying question in Hebrew (e.g. “רק לוודא – האם תרצה בדיקה ללא עלות, כן או לא?”).  
                    – Only when the intention is crystal-clear may you continue.

                    2. Follow the conversation flow below exactly.  
                    – Do not skip a step.  
                    – Never offer anything not described.  
                    – If the caller says anything unrelated, answer briefly:  
                        “אין לי מידע על זה כרגע, אבל אשמח לקשר אותך לסוכן.”  
                        then return to the current step.

                    3. If at any point the caller becomes abusive or unreachable, say:  
                    “תודה על הזמן, יום טוב,” and hang up.

                    CONVERSATION FLOW
                    ────────────────────────────────────────

                    Step 0  ❱❱ Opening  
                    Say:  
                    » “שלום, מדבר גפן, העוזר הדיגיטלי של גפן ביטוחים. איך אתה מרגיש?”

                    Step 1  ❱❱ Purpose & CTA  
                    Say:  
                    » “ראינו שעברה יותר משנה מאז בדקת את הכיסויים שלך. חשוב לוודא שהם עדיין מתאימים לך ולמשפחה. האם תרצה בדיקה מחדש, ללא עלות וללא התחייבות?”

                    * If caller’s intention is unclear → ask a yes/no clarification (see RULE 1).

                    Step 2  ❱❱ Positive branch (caller interested)  
                    Say:  
                    » “הבדיקה לוקחת כ-10 דקות. נבדוק כיסויים כפולים, חסרים או מיותרים, ונציע דרכי שיפור או חיסכון.”  
                    » “מתי נוח לך לשוחח עם סוכן – מחר בבוקר או בצהריים?”  
                     • *בוקר- בין השעות שמונה וחצי עד אחד עשרה וחצי
                    צהריים- בין השעות שתיים עשרה עד ארבע

                    –– If caller names a specific hour, confirm in range:  
                    » “אני מעביר את הבקשה שלך לסוכן שיצור איתך קשר בטווח השעות שביקשת.”

                    –– After time chosen, close:  
                    » “אני מעביר את הפנייה שלך לסוכן שיצור איתך קשר בטווח הזמן שדיברנו. לשינוי זמן אנחנו כאן תמיד. תודה ולהתראות”

                    Step 3  ❱❱ Negative branch (caller refuses)  
                    Say FIRST-REFUSAL text:  
                    » “מבין לגמרי. חשוב לי לציין את החשיבות של בדיקה פעם בשנה – זה יכול לחסוך הרבה כסף! תרצה לשמוע עוד מהסוכן שלנו מחר בבוקר?”

                    ★★ STOP and WAIT for the answer ★★

                    * If caller still refuses →  
                    Say: “תודה רבה על זמנך, שיהיה לך יום מצוין, ולהתראות.”  
                    End the call.

                    * If caller now interested (כן/yes) →  
                    Go to Step 2 (Positive branch).

                    Step 4  ❱❱ Memory lapse branch  
                    If caller says “לא זוכר / אולי / לא בטוח” before accepting or refusing:  
                    Say:  
                    » “יכול להיות, זה היה לפני יותר משנה. זו בדיקה ללא התחייבות – רק כדי לוודא שאתה לא משלם על מה שלא צריך. האם תרצה שנקבע לך שיחה עם סוכן?”

                    –– Proceed based on clear yes/no answer (apply RULE 1 if unclear).

                    END OF FLOW

                    
                    Remember:
                    Maintain a pleasant, respectful, and humane tone.

                    Ask closed questions (yes/no) to allow for clear automatic classification.

                    At each exit, provide a brief summary of the action taken.

                    If the customer specifies an exact time – it is important to make it clear that you are transferring the request to an agent who will contact them during the hours they requested, and not at the specific time.

                    If during the conversation the customer changes their mind – it is important to refer only to their final answer for the purpose of making a decision.
                                    """)

# VOICE = 'alloy'
# VOICE = 'sage'
VOICE = 'echo'
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
    batch_id = str(uuid.uuid4())
    # Store mapping in cache
    cache.set(batch_id, {"call_sids": {phone_number: call_sid}}, timeout=3600)
    
    
    # cache_key = f"{call_sid}"
    # cache._cache[cache_key] = call_sid
        
    # <Say> punctuation to improve text-to-speech flow
    # response.say("HEY")
    # response.pause(length=1)
    # response.say("start")
    
    # Get host from request
    host = request.get_host()
    
    connect = Connect()
    connect.stream(url=f'wss://{host}/media-stream/{batch_id}/{phone_number}')

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
        batch_id = self.scope['url_route']['kwargs'].get('batch_id')
        phone_number = self.scope['url_route']['kwargs'].get('phone_number')
        # Retry fetching call_sid from cache
        try:
            for attempt in range(5):  # Retry up to 5 times
                with cache_lock:
                    cache_data = cache.get(batch_id)
                    cache_key = f"system_message_{batch_id}_{phone_number}"
                    self.system_message = cache.get(cache_key) or SYSTEM_MESSAGE_MAN
                    logger.info(f"Batch cache data: {cache_data}")

                    if cache_data and "call_sids" in cache_data:
                        self.call_sid = cache_data["call_sids"].get(phone_number)

                if self.call_sid:
                    logger.info(f"Retrieved call_sid from cache: {self.call_sid}")
                    break
                else:
                    logger.warning(f"Attempt {attempt + 1}: call_sid not found for phone number: {phone_number} in batch: {batch_id}")
                    await asyncio.sleep(0.5)  # Wait for 500ms before retrying
        except Exception as e:
            print (f"ERROR {e}")
        if not self.call_sid:
            logger.error(f"call_sid not found for phone number: {phone_number} in batch: {batch_id}")
        else:
            logger.info(f"Successfully retrieved call_sid: {self.call_sid}")
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
                # Extract the actual call_sid or batch_id from the stored value
                # This handles both normal call_sid and the unusual format with ':None:' prefix
                actual_sid = self.call_sid.split(':')[-1] if ':' in self.call_sid else self.call_sid
                logger.info(f"Disconnect: Attempting to find Call object with actual_sid: {actual_sid}")
                # Try to find the call by call_sid first
                try:
                    call = await sync_to_async(Call.objects.get)(call_sid=actual_sid)
                except Call.DoesNotExist:
                    logger.info(f"Disconnect: Call object with SID {actual_sid} NOT FOUND in DB.") # ADD THIS

                    # If not found by call_sid, try to find the most recent call with matching batch_id
                    # (if the value appears to be a UUID)
                    if len(actual_sid) > 30:  # Rough check if it looks like a UUID
                        try:
                            # Get the most recent call that hasn't been updated yet
                            call = await sync_to_async(lambda: Call.objects.filter(
                                call_sid__in=twilio_client.calls.list(status='completed', limit=10)
                            ).order_by('-created_at').first())()
                            
                            if not call:
                                logger.warning(f"No matching call found for update with sid: {actual_sid}")
                                return
                        except Exception as e:
                            logger.error(f"Error finding recent call: {e}")
                            return
                    else:
                        logger.warning(f"No valid call_sid or batch_id found: {actual_sid}")
                        return
                    
                # Update the call record
                call.total_duration = formatted_duration
                call.status = 'completed'
                
                # Save conversation data if available
                if hasattr(self, 'conversation_data'):
                    for user_speech, ai_response in zip(
                        self.conversation_data.get("user_speech", []), 
                        self.conversation_data.get("ai_responses", [])
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
                logger.info(f"Successfully updated call with duration: {formatted_duration}")
                # Analyze the call and save the conclusion
                logger.info(f"Disconnect: Preparing to analyze call ID: {call.id}. Checking conversation data on consumer: {getattr(self, 'conversation_data', 'Not present')}")

                conclusion = await sync_to_async(analyze_call_summary)(call)
                call.conclusion = conclusion
                await sync_to_async(call.save)()
                logger.info(f"Call conclusion saved: {conclusion}")
            except Exception as e:
                logger.error(f"Error updating call duration: {e}")
            logger.debug(f"Conversation data: {self.conversation_data}")
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
                "turn_detection": {"type": "server_vad",
                                #    "eagerness": "low",
                                   "threshold": 0.8,
                                   },
                "input_audio_format": "g711_ulaw",
                "output_audio_format": "g711_ulaw",
                "voice": VOICE,
                "instructions": self.system_message,
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
        # logger.info(f"Sending session update: {json.dumps(session_update)}")
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
        # call = Call.objects.get(call_sid='CAdb653fb3fff995b4a387b03fce4780c5')
        # analyze_call_summary(call)
        # return
        # Parse the request body
        data = json.loads(request.body)
        to_number = data.get('phone_number')
        logger.info(f"Outbound call to number: {to_number}")
        if not to_number:
            return JsonResponse({"error": "Phone number is required"}, status=400)

        # Generate a unique batch_id for this call
        batch_id = str(uuid.uuid4())
        # Store mapping in cache
        cache.set(batch_id, {"call_sids": {to_number: None}, "completed": 0, "total": 1}, timeout=3600)

        # Get host from request for webhook URL
        # host = 'list-coating-alone-bp.trycloudflare.com'
        host = 'web-production-7204.up.railway.app'
        # Create the TwiML for the outbound call
        response = VoiceResponse()
        connect = Connect()
        connect.stream(url=f'wss://{host}/media-stream/{batch_id}/{to_number}')
        response.append(connect)
        # Make the outbound call
        call = twilio_client.calls.create(
            to=to_number,
            from_=TWILIO_PHONE_NUMBER_NEW,
            twiml=str(response),
            status_callback=f'https://{host}/call-status-outbound/?batch_id={batch_id}',
            status_callback_event=['initiated', 'ringing', 'in-progress', 'completed'],
            status_callback_method='POST'
        )

        # Update cache with the call_sid
        batch_cache = cache.get(batch_id) or {}
        if "call_sids" not in batch_cache:
            batch_cache["call_sids"] = {}
        batch_cache["call_sids"][to_number] = call.sid
        cache.set(batch_id, batch_cache, timeout=3600)

        # Wait for up to 10 seconds to check if the call is answered
        for _ in range(20):
            call_status = cache.get(f"call_status_{call.sid}")
            if call_status == "in-progress":
                logger.info(f"Call {call.sid} answered by {to_number}.")
                return JsonResponse({
                    "success": True,
                    "call_sid": call.sid,
                    "batch_id": batch_id,
                    "status": "answered",
                    "message": f"Call answered by {to_number}"
                })
            time.sleep(1)  # Check every second

        # If the call is still ringing after 10 seconds, mark it as "busy"
        logger.info(f"Call {call.sid} not answered within 10 seconds. Marking as busy.")
        call_record = Call.objects.get(call_sid=call.sid)
        call_record.status = "busy"
        call_record.save()

        return JsonResponse({
            "success": True,
            "call_sid": call.sid,
            "batch_id": batch_id,
            "status": "busy",
            "message": f"Call to {to_number} marked as busy"
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
    # logger.info(f"Call status update received: {call_status} for CallSid: {call_sid}")

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

@csrf_exempt
@require_http_methods(["POST"])
def call_status_callback_outbound(request):
    """
    Handle Twilio call status callbacks.
    This endpoint will receive updates about the call status.
    """
    call_sid = request.POST.get('CallSid')
    call_status = request.POST.get('CallStatus')
    phone_number = request.POST.get("To")
    caller_id = request.POST.get("From")
    batch_id = request.GET.get("batch_id")  # Pass batch_id when initiating the call
    # logger.info(f"Call status update received: {call_status} for CallSid: {call_sid} ,Batch ID: {batch_id}")

    if not call_sid:
        return JsonResponse({"error": "CallSid is required"}, status=400)
    try:
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
                # Update the existing record
                call.status = call_status
                if phone_number and len(phone_number) > 3:
                    call.phone_number = phone_number
                if caller_id and len(caller_id) > 3:
                    call.caller_id = caller_id
                call.save()
                
            # Add to cache with just the call_sid as the key
            cache_key = call_sid
            cache._cache[cache_key] = call_sid
            # Update the batch status in the cache
            if batch_id:
                batch_status = cache.get(batch_id) or {}
                if call_status in ["completed", "no-answer", "busy", "failed"]:
                    batch_status[call_status] = batch_status.get(call_status, 0) + 1
                cache.set(batch_id, batch_status, timeout=3600)
            
    except Exception as e:
        logger.error(f"Error updating call status for {call_sid}: {e}")
    
    return HttpResponse(status=200)

        
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
    
@csrf_exempt
@require_http_methods(["POST"])
def bulk_calls(request):
    """Handle bulk calls from a CSV file."""
    if request.method == 'POST':
        # Call.objects.all().delete()
        csv_file = request.FILES.get('file')
        if not csv_file:
            return JsonResponse({"error": "No file provided"}, status=400)

        try:
            # Read the CSV file using pandas with UTF-8 encoding
            df = pd.read_excel(csv_file)
            
            # Check for required columns
            if 'שם' not in df.columns or 'טלפון' not in df.columns:
                return JsonResponse({
                    "message": "CSV must contain 'name' and 'phone number' columns"
                }, status=400)

            # Count total calls to be made
            total_calls = len(df)
            job_id = str(uuid.uuid4())  # Generate a unique job ID

            # Process the file in chunks of 4 calls at a time
            for i in range(0, len(df), 3):
                chunk = df.iloc[i:i + 3]
                calls_data = []
                batch_id = str(uuid.uuid4())  # Unique ID for this batch
                for _, row in chunk.iterrows():
                    name=str(row['שם'])
                    if len(name)>1 and name != 'nan':
                        # system_message=SYSTEM_MESSAGE_MAN
                        system_message =f"""
                  Speak in Hebrew with a warm, upbeat, and reassuring tone. Use a natural Israeli male accent
               with clear, precise pronunciation. Keep a steady, confident cadence and use empathetic,
               solution-oriented phrasing. Focus on positive language and next steps.
                As a male, provide your response exclusively addressing men, using male pronouns and language for them while maintaining male pronouns and language for yourself.
                  System:
                    You are “גפן”, the digital voice assistant for “גפן ביטוחים”.

                    LANGUAGE
                    * All spoken output to the caller MUST be in Hebrew.
                    * Internal reasoning stays hidden; the customer only hears the Hebrew lines.

                    GENERAL RULES
                    1. Never guess.  
                    – If you are NOT 100 % certain whether the caller accepted or refused an offer, ask a short clarifying question in Hebrew (e.g. “רק לוודא – האם תרצה בדיקה ללא עלות, כן או לא?”).  
                    – Only when the intention is crystal-clear may you continue.

                    2. Follow the conversation flow below exactly.  
                    – Do not skip a step.  
                    – Never offer anything not described.  
                    – If the caller says anything unrelated, answer briefly:  
                        “אין לי מידע על זה כרגע, אבל אשמח לקשר אותך לסוכן.”  
                        then return to the current step.

                    3. If at any point the caller becomes abusive or unreachable, say:  
                    “תודה על הזמן, יום טוב,” and hang up.

                    CONVERSATION FLOW
                    ────────────────────────────────────────

                    Step 0  ❱❱ Opening  
                    Say:  
                    » “שלום, מדבר גפן, העוזר הדיגיטלי של גפן ביטוחים. איך אתה מרגיש (שם הלקוח: {name})?”

                    Step 1  ❱❱ Purpose & CTA  
                    Say:  
                    » “ראינו שעברה יותר משנה מאז בדקת את הכיסויים שלך. חשוב לוודא שהם עדיין מתאימים לך ולמשפחה. האם תרצה בדיקה מחדש, ללא עלות וללא התחייבות?”

                    * If caller’s intention is unclear → ask a yes/no clarification (see RULE 1).

                    Step 2  ❱❱ Positive branch (caller interested)  
                    Say:  
                    » “הבדיקה לוקחת כ-10 דקות. נבדוק כיסויים כפולים, חסרים או מיותרים, ונציע דרכי שיפור או חיסכון.”  
                    » “מתי נוח לך לשוחח עם סוכן – מחר בבוקר או בצהריים?”  
                     • *בוקר- בין השעות שמונה וחצי עד אחד עשרה וחצי
                    צהריים- בין השעות שתיים עשרה עד ארבע

                    –– If caller names a specific hour, confirm in range:  
                    » “אני מעביר את הבקשה שלך לסוכן שיצור איתך קשר בטווח השעות שביקשת.”

                    –– After time chosen, close:  
                    » “אני מעביר את הפנייה שלך לסוכן שיצור איתך קשר בטווח הזמן שדיברנו. לשינוי זמן אנחנו כאן תמיד. תודה ולהתראות”

                    Step 3  ❱❱ Negative branch (caller refuses)  
                    Say FIRST-REFUSAL text:  
                    » “מבין לגמרי. חשוב לי לציין את החשיבות של בדיקה פעם בשנה – זה יכול לחסוך הרבה כסף! תרצה לשמוע עוד מהסוכן שלנו מחר בבוקר?”

                    ★★ STOP and WAIT for the answer ★★

                    * If caller still refuses →  
                    Say: “תודה רבה על זמנך, שיהיה לך יום מצוין, ולהתראות.”  
                    End the call.

                    * If caller now interested (כן/yes) →  
                    Go to Step 2 (Positive branch).

                    Step 4  ❱❱ Memory lapse branch  
                    If caller says “לא זוכר / אולי / לא בטוח” before accepting or refusing:  
                    Say:  
                    » “יכול להיות, זה היה לפני יותר משנה. זו בדיקה ללא התחייבות – רק כדי לוודא שאתה לא משלם על מה שלא צריך. האם תרצה שנקבע לך שיחה עם סוכן?”

                    –– Proceed based on clear yes/no answer (apply RULE 1 if unclear).

                    END OF FLOW

                    
                    Remember:
                    Maintain a pleasant, respectful, and humane tone.

                    Ask closed questions (yes/no) to allow for clear automatic classification.

                    At each exit, provide a brief summary of the action taken.

                    If the customer specifies an exact time – it is important to make it clear that you are transferring the request to an agent who will contact them during the hours they requested, and not at the specific time.

                    If during the conversation the customer changes their mind – it is important to refer only to their final answer for the purpose of making a decision.
                                    """
                                    
                                    
            #             system_message = f""""
            #        Speak in Hebrew with a warm, upbeat, and reassuring tone. Use a natural Israeli male accent
            #    with clear, precise pronunciation. Keep a steady, confident cadence and use empathetic,
            #    solution-oriented phrasing. Focus on positive language and next steps.
            #     As a male, provide your response exclusively addressing men, using male pronouns and language for them while maintaining male pronouns and language for yourself.
            #       System:
            #         פרומפט (אתה “גפן” – עוזר קולי דיגיטלי של סוכנות גפן ביטוחים)
            #         תפקיד: לנהל שיחה יזומה עם לקוחות גברים שבדקו ביטוחים אצלנו לפני יותר משנה.

            #         1. פתיחה
            #         “{name} שלום, מדבר גפן, העוזר הדיגיטלי של גפן ביטוחים. מה שלומך היום?”

            #         2. מטרה וקריאה לפעולה
            #         “ראינו שעברה יותר משנה מאז בדקת את הכיסויים שלך. חשוב לוודא שהם עדיין מתאימים לך ולמשפחה. האם תרצה בדיקה מחדש, ללא עלות וללא התחייבות?”

            #         3. זרימות עיקריות
            #         חיובי
            #         “הבדיקה לוקחת כ-10 דקות. נבדוק כיסויים כפולים, חסרים או מיותרים, ונציע דרכי שיפור או חיסכון.”

            #         “מתי נוח לך לשוחח עם סוכן – מחר בוקר או צהריים?”

            #         “אני מעביר את הפנייה שלך לסוכן שיצור איתך קשר בטווח הזמן שדיברנו. לשינוי זמן אנחנו כאן תמיד.”
            #         *בוקר- בין השעות שמונה וחצי עד אחד עשרה וחצי
            #         צהריים- בין השעות שתיים עשרה עד ארבע

            #         אם הלקוח מתייחס לשעה מסוימת (כמו 10:00):
            #         “אין בעיה {name}, אני מעביר את הבקשה שלך לסוכן שיצור איתך קשר בטווח השעות שביקשת.”

            #         סירוב
            #         “מבין לגמרי. אם בעתיד תרצה לבדוק שוב, תוכל לפנות אלינו. תודה שענית, שיהיה לך יום מצוין!”

            #         לא זוכר
            #         “יכול להיות, זה היה לפני יותר משנה. זו בדיקה ללא התחייבות – רק כדי לוודא שאתה לא משלם על מה שלא צריך. האם תרצה שנקבע לך שיחה עם סוכן?”

            #         תזכור:
            #         שמור על טון נעים, מכבד ואנושי.

            #         שאל שאלות סגורות (כן/לא) כדי לאפשר סיווג אוטומטי ברור.

            #         בכל יציאה תן סיכום קצר של הפעולה שננקטה.

            #         אם הלקוח מציין שעה מדויקת – חשוב להבהיר שאתה מעביר את הבקשה לסוכן שיצור איתו קשר בטווח השעות שביקש, ולא בשעה הספציפית.

            #         אם במהלך השיחה הלקוח משנה את דעתו – חשוב להתייחס לתשובתו הסופית בלבד לצורך קבלת החלטה.
            #                         """
                    else:
                        system_message = SYSTEM_MESSAGE_MAN
                    phone_number = "+972" + str(int(row['טלפון']))
                    calls_data.append({
                    "name": name,
                    "phone_number": phone_number,
                    "batch_id": batch_id,
                    "system_message": system_message
                })
                # Save batch to cache or database
                 # Set the system message cache individually (this part is okay)
                cache.set(f"system_message_{batch_id}_{phone_number}", system_message, timeout=3600)

                # --- Set the main batch cache entry ONCE per batch ---
                # Initialize with an empty call_sids dictionary
                initial_batch_status = {
                    "calls": calls_data,  # Store the list of calls for potential reference
                    "completed": 0,
                    "no-answer": 0,
                    "busy": 0,
                    "total": len(calls_data),
                    "call_sids": {} # Initialize the dictionary where handle_call will add SIDs
                }
                cache.set(batch_id, initial_batch_status, timeout=3600) # Use a timeout
                logger.info(f"Initialized cache for batch {batch_id} with {len(calls_data)} calls.")
                logger.debug(f"Initial batch status for {batch_id}: {initial_batch_status}")

                # --- Now make the calls for this batch ---
                # No need to check cache status here like before, just make calls
                logger.info(f"Processing batch {batch_id} with {len(calls_data)} calls.")
                make_bulk_outbound_calls(calls_data) # Pass the prepared list


            return JsonResponse({
                "success": True,
                "message": "File uploaded successfully",
                "job_id": job_id,
                "total_calls": total_calls
            })
        
        except pd.errors.EmptyDataError:
            return JsonResponse({
                "message": "The uploaded file is empty"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "message": f"Error processing file: {str(e)}"
            }, status=500)



from concurrent.futures import ThreadPoolExecutor, as_completed

def make_bulk_outbound_calls(calls_data):
    """
    Helper function to handle outbound calls in parallel.
    """
    def handle_call(call):
        """
        Handle a single call, including initiating the call and monitoring for a timeout.
        """
        with cache_lock:
            batch_status = cache.get(call['batch_id']) or {}
            if "call_sids" in batch_status and call['phone_number'] in batch_status["call_sids"]:
                logger.info(f"Skipping call to {call['phone_number']} as it already has a call_sid.")
                return

        try:
            # host = 'list-coating-alone-bp.trycloudflare.com'
            host = 'web-production-7204.up.railway.app'
            # Create the TwiML for the outbound call
            response = VoiceResponse()
            connect = Connect()
            connect.stream(url=f'wss://{host}/media-stream/{call["batch_id"]}/{call["phone_number"]}')
            response.append(connect)
            # logger.info(f"TwiML being sent to Twilio: {str(response)}")

            # Make the outbound call
            twilio_call = twilio_client.calls.create(
                to=call['phone_number'],
                from_=TWILIO_PHONE_NUMBER_NEW,
                twiml=str(response),
                status_callback=f'https://{host}/call-status-outbound/?batch_id={call["batch_id"]}',
                status_callback_event=['initiated', 'ringing', 'in-progress', 'completed', 'no-answer', 'busy', 'failed'],
                status_callback_method='POST'
            )
            with cache_lock:
            # Read the current status *inside* the lock
                batch_status = cache.get(call['batch_id']) or {}

                # Modify the dictionary
                # Ensure 'call_sids' key exists
                if "call_sids" not in batch_status:
                    batch_status["call_sids"] = {}
                # Add or update the call_sid for this phone number
                batch_status["call_sids"][call['phone_number']] = twilio_call.sid

                # Write the updated status back *inside* the lock
                cache.set(call['batch_id'], batch_status, timeout=3600)
                logger.info(f"Updated batch cache with call_sid: {twilio_call.sid} for phone number: {call['phone_number']}")
                logger.debug(f"Current batch status in cache for {call['batch_id']}: {batch_status}") # Add for debugging


            # Monitor the call for up to 20 seconds
            for _ in range(20):
                call_status = twilio_client.calls(twilio_call.sid).fetch().status
                if call_status == "in-progress":
                    logger.info(f"Call {twilio_call.sid} answered by {call['phone_number']}.")
                    break
                time.sleep(1)  # Check every second
            # If the call is still ringing after 20 seconds, hang up
            if call_status != "in-progress":
                logger.info(f"Call {twilio_call.sid} not answered within 20 seconds. Hanging up.")
                twilio_client.calls(twilio_call.sid).update(status="completed")
                return
            # Monitor the call for up to 5 minutes (300 seconds)
            start_time = time.time()
            print ("Start the time!!!!")
            while True:
                call_status = twilio_client.calls(twilio_call.sid).fetch().status
                if call_status == "in-progress":
                    elapsed_time = time.time() - start_time
                    if elapsed_time > 300:  # 5 minutes in seconds
                        logger.info(f"Call {twilio_call.sid} exceeded 10 minutes. Hanging up.")
                        twilio_client.calls(twilio_call.sid).update(status="completed")
                        return
                elif call_status in ["completed", "failed", "busy", "no-answer"]:
                    logger.info(f"Call {twilio_call.sid} ended with status: {call_status}.")
                    return
                time.sleep(1)  # Check every second


        except Exception as e:
            logger.error(f"Failed to initiate or monitor call to {call['name']} at {call['phone_number']}: {e}")

     # Use ThreadPoolExecutor to handle calls in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(handle_call, call) for call in calls_data]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error(f"Error in call handling: {e}")