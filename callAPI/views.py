# callAPI/views.py

import base64
import os
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import requests
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from .models import Call, ConversationTurn
from rest_framework.decorators import api_view
import openai
from dotenv import load_dotenv
import threading

load_dotenv()

# Set your OpenAI API key
OPENAI_API_KEY= settings.OPENAI_API_KEY
openai.api_key = OPENAI_API_KEY
# Initialize Twilio client
twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


@csrf_exempt
@api_view(['POST'])
def make_call(request):
    """
    Initiate an outbound call by creating a Call object and using Twilio's API.
    """
    if request.method == 'POST':
        phone_number = request.data.get('phone_number')
        print("phone_number", phone_number)
        TWILIO_PHONE_NUMBER_NEW = os.getenv('TWILIO_PHONE_NUMBER_NEW')
        print(TWILIO_PHONE_NUMBER_NEW)
        print(type(TWILIO_PHONE_NUMBER_NEW))
        if not phone_number:
            return JsonResponse({'error': 'Phone number required'}, status=400)
        
        # Create a new call record
        call_obj = Call.objects.create(
            phone_number=phone_number,
            caller_id=settings.TWILIO_PHONE_NUMBER_NEW
        )
        print("New call obg creadted")
        # Use PUBLIC_URL from environment for a publicly accessible callback URL.
        # public_url = "https://0b22-94-188-131-83.ngrok-free.app"
        public_url = "https://web-production-7204.up.railway.app"
        if public_url:
            callback_url = f'{public_url}/api/call/{call_obj.id}/twiml/'
            status_callback_url = f'{public_url}/api/call/{call_obj.id}/status/'
        else:
            # Fallback: This will work only if your server is publicly accessible.
            callback_url = request.build_absolute_uri(f'/api/call/{call_obj.id}/twiml/')
            status_callback_url = request.build_absolute_uri(f'/api/call/{call_obj.id}/status/')
        print("Start calling")
        if not os.path.exists(settings.MEDIA_ROOT):
            os.makedirs(settings.MEDIA_ROOT, exist_ok=True)  # Safe creation

        # try:
        #     tts_completion = openai.audio.speech.create(
        #         model="gpt-4o-mini-tts",
        #         voice="alloy",  # Optionally remove if you prefer the default voice.
        #         instructions=(
        #             "Speak in Hebrew with a warm, upbeat, and reassuring tone. Use a natural Israeli accent "
        #             "with clear, precise pronunciation. Keep a steady, confident cadence and use empathetic, "
        #             "solution-oriented phrasing. Focus on positive language and next steps."
        #         ),
        #         input="היי אני העוזר הוירטואלי של מושיק"
        #     )
        #     welcome_audio_filename = f"tts'_welcome_{call_obj.id}.mp3"
        #     audio_filepath = os.path.join(settings.MEDIA_ROOT, welcome_audio_filename)
        #     tts_completion.stream_to_file(audio_filepath)
            
        # except Exception as e:
        #     print("TTS error:", e)
        import shutil

        # Ensure ummm.wav exists in MEDIA_ROOT
        umm_filepath = os.path.join(settings.MEDIA_ROOT, "ummm.wav")
        if not os.path.exists(umm_filepath):
            source_path = os.path.join(os.path.dirname(__file__), "static", "ummm.wav")  # Adjust source path
            shutil.copy(source_path, umm_filepath)

        # Ensure Hey.wav exists in MEDIA_ROOT
        hey_filepath = os.path.join(settings.MEDIA_ROOT, "Hey.wav")
        if not os.path.exists(hey_filepath):
            source_path = os.path.join(os.path.dirname(__file__), "static", "Hey.wav")  # Adjust source path
            shutil.copy(source_path, hey_filepath)
        try:
            umm_filepath = os.path.join(settings.MEDIA_ROOT, "ummm.wav")
            if os.path.exists(umm_filepath):
                print(f"File exists at: {umm_filepath}")
            else:
                print("File not found!")
        except Exception as e:
            print("Error in ummm.wav file:", e)
            
            
        try:
            hey_filepath = os.path.join(settings.MEDIA_ROOT, "Hey.wav")
            if os.path.exists(hey_filepath):
                print(f"File exists at: {hey_filepath}")
            else:
                print("File not found!")
        except Exception as e:
            print("Error in Hey.wav file:", e)
       
        if os.path.exists(settings.MEDIA_ROOT):
            print("Files in MEDIA_ROOT:")
            for file_name in os.listdir(settings.MEDIA_ROOT):
                print(file_name)
        else:
            print("MEDIA_ROOT directory does not exist:", settings.MEDIA_ROOT)
        
        # Initiate the outbound call using Twilio
        try:
            
            twilio_call = twilio_client.calls.create(
                to=phone_number,
                from_=TWILIO_PHONE_NUMBER_NEW,
                url=callback_url,
                status_callback=status_callback_url,
                status_callback_event=['completed', 'failed']
            )
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        
        # Save the Twilio Call SID
        call_obj.call_sid = twilio_call.sid
        call_obj.save()
        
        return JsonResponse({'message': 'Call initiated', 'call_id': call_obj.id})
    else:
        return JsonResponse({'error': 'POST request required'}, status=400)


@csrf_exempt
def call_twiml(request, call_id):
    """
    Generate TwiML for the ongoing call.
    Immediately play a filler ("ummm…") and concurrently start generating the GPT response.
    Then, redirect to the play_response endpoint to play the generated GPT answer audio.
    """
    # public_url = "https://0b22-94-188-131-83.ngrok-free.app"
    public_url = "https://web-production-7204.up.railway.app"
    call_obj = get_object_or_404(Call, id=call_id)
    response = VoiceResponse()
    
    speech_result = request.POST.get('SpeechResult') or request.GET.get('SpeechResult')
    partial_speech = request.POST.get('PartialSpeechResult') or request.GET.get('PartialSpeechResult')
    
    if partial_speech:
        print("Partial speech received:", partial_speech)
    
    if speech_result:
        print("User said:", speech_result)
        ConversationTurn.objects.create(call=call_obj, text=speech_result, is_ai=False)
        
        # Build conversation history.
        conversation = [{
            "role": "system",
            "content": (
                "Well, you're an AI assistant that speaks regular Hebrew, like, in a totally chill way "
                "and with good vibes. Throw in some Israeli slang (like 'sababa') and keep a good atmosphere, bro."
            )
        }]
        for turn in call_obj.conversation.all():
            role = "assistant" if turn.is_ai else "user"
            conversation.append({"role": role, "content": turn.text})
        
        # Start background thread to generate GPT response and TTS audio.
        thread = threading.Thread(target=generate_gpt_audio, args=(call_obj, conversation, public_url))
        thread.start()
        
        # Immediately play the filler audio.
        try:
            filler_filename = "ummm.wav"
            filler_url = f"{public_url}/media/{filler_filename}"
            print("Playing filler audio:", filler_url)
            response.play(filler_url)
        except Exception as e:
            print("Filler audio error:", e)
            response.say("ummm...")
        
        # After the filler, redirect to the play_response endpoint.
        thread.join()
        try:
            audio_filename = f"tts_{call_obj.id}.mp3"
            audio_url = f"{public_url}/media/{audio_filename}"
            print("Playing generated audio:", audio_url)
            response.play(audio_url)
        except Exception as e:
            print("Error playing audio:", e)
            response.say("מצטער, אירעה שגיאה בהשמעת התגובה.", language="he-IL")
    
    else:
        response.pause(length=1)
        try:
            welcome_filename = "Hey.wav"
            welcome_url = f"{public_url}/media/{welcome_filename}"
            print("Playing welcome audio:", welcome_url)
            response.play(welcome_url)
        except Exception as e:
            print("Welcome audio error:", e)
            response.say("Hi")
    
    # Set up a <Gather> element for continuous speech capture.
    gather = Gather(
        speechModel="default",
        input='speech',
        language='he-IL',
        action=request.build_absolute_uri(),
        timeout=0.5,
        speechTimeout=0.5,
        hints="שלום, מה המצב, הלו, היי"
    )
    response.append(gather)
    response.redirect(request.build_absolute_uri())
    
    return HttpResponse(response.to_xml(), content_type='application/xml')
def generate_gpt_audio(call_obj, conversation, public_url):
    """
    Function to generate the GPT response and TTS audio.
    This runs in a background thread.
    """
    try:
        # Generate AI response using ChatCompletion (text)
        completion = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation,
            temperature=0.7,
            max_tokens=100
        )
        ai_response = completion.choices[0].message.content.strip()
        print("Generated ai_response:", ai_response)
    except Exception as e:
        print("Error with GPT response:", e)
        ai_response = "מצטער איני יכול לעזור כרגע"
    
    # Save the AI response.
    ConversationTurn.objects.create(call=call_obj, text=ai_response, is_ai=True)
    
    # Convert the AI response to audio using GPT-4o-Audio-Preview.
    try:
        tts_completion = openai.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            instructions=(
                "Speak in Hebrew with a warm, upbeat, and reassuring tone. Use a natural Israeli accent "
                "with clear, precise pronunciation. Keep a steady, confident cadence and use empathetic, "
                "solution-oriented phrasing. Focus on positive language and next steps."
            ),
            input=ai_response
        )
        audio_filename = f"tts_{call_obj.id}.mp3"
        audio_filepath = os.path.join(settings.MEDIA_ROOT, audio_filename)
        tts_completion.stream_to_file(audio_filepath)
        print("TTS audio generated at:", audio_filepath)
    except Exception as e:
        print("TTS error:", e)
        
@csrf_exempt
def play_response(request, call_id):
    """
    Endpoint to check if GPT+TTS audio is ready.
    If ready, play it; if not, pause and redirect to itself.
    """
    public_url = "https://0b22-94-188-131-83.ngrok-free.app"
    call_obj = get_object_or_404(Call, id=call_id)
    response = VoiceResponse()
    
    audio_filename = f"tts_{call_obj.id}.mp3"
    audio_filepath = os.path.join(settings.MEDIA_ROOT, audio_filename)
    
    if os.path.exists(audio_filepath):
        audio_url = f"{public_url}{settings.MEDIA_URL}{audio_filename}"
        print("Playing GPT response audio:", audio_url)
        response.play(audio_url)
    else:
        # Audio not ready yet—pause briefly and redirect back.
        print("GPT response audio not ready yet. Waiting...")
        response.pause(length=1)
        response.redirect(request.build_absolute_uri())
    
    return HttpResponse(response.to_xml(), content_type="application/xml")

@csrf_exempt
@api_view(['POST'])
def call_status(request, call_id):
    """
    Handle call status updates from Twilio.
    """
    call_obj = get_object_or_404(Call, id=call_id)
    call_status = request.POST.get('CallStatus')
    if call_status:
        call_obj.status = call_status
        call_obj.save()
    return HttpResponse("Status updated")


def get_calls(request):
    """
    API endpoint to list all calls.
    """
    calls = Call.objects.all().values()
    return JsonResponse(list(calls), safe=False)


def get_conversation(request, call_id):
    """
    API endpoint to retrieve the conversation for a specific call.
    """
    call_obj = get_object_or_404(Call, id=call_id)
    conversation = list(call_obj.conversation.all().values())
    return JsonResponse(conversation, safe=False)



@csrf_exempt
def partial_callback(request):
    """Handle partial speech results from Twilio."""
    print("Request POST data: %s", request.POST)
    partial_speech = request.POST.get('PartialSpeechResult')
    if partial_speech:
        print("Partial speech detected:", partial_speech)
        # Optionally: Process partial text here (e.g., send to OpenAI early)
    return HttpResponse(status=200)  # Empty response (TwiML not required)