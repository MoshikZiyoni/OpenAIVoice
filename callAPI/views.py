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
        # public_url = "https://d650-94-188-131-83.ngrok-free.app"
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

        # hey_file_path = os.path.join(settings.MEDIA_ROOT, 'Hey.mp3')

        # # Check if Hey.mp3 exists
        # if not os.path.exists(hey_file_path):
        #     print("Hey.mp3 file does not exist at:", hey_file_path)
        # else:
        #     print("Hey.mp3 file exists at:", hey_file_path)
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
    Generate TwiML for the ongoing call. Process the caller's speech with OpenAI,
    convert the AI response to audio using GPT-4o-Audio-Preview, and play the audio.
    """
    # public_url = "https://d650-94-188-131-83.ngrok-free.app"
    public_url = "https://web-production-7204.up.railway.app"
    call_obj = get_object_or_404(Call, id=call_id)
    response = VoiceResponse()
    
    # Capture the transcription provided by Twilio
    speech_result = request.POST.get('SpeechResult') or request.GET.get('SpeechResult')
    if speech_result:
        # Log/print the user's speech for debugging
        print("User said:", speech_result)
        
        # Save the human input
        ConversationTurn.objects.create(call=call_obj, text=speech_result, is_ai=False)
        
        # Build conversation history (system prompt + prior turns)
        conversation = [
            {
            "role": "system",
            "content": (
                "Well, you're an AI assistant that speaks regular Hebrew, like, in a totally chill way and with good vibes."
                "Throw in some Israeli slang here and there (like 'sababa') and keep a good atmosphere, bro, be confident."
            )
            }
        ]
        for turn in call_obj.conversation.all():
            role = "assistant" if turn.is_ai else "user"
            conversation.append({"role": role, "content": turn.text})
        
        # Generate AI response using ChatCompletion (for text)
        try:
            completion = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=conversation,
                temperature=0.7,
                max_tokens=100
            )
            ai_response = completion.choices[0].message.content.strip()
            print("ai_response: " , ai_response)
        except Exception as e:
            print("Error with gpt-4o-mini", e)
            ai_response = "מצטער איני יכול לעזור כרגע"
        
        # Save the AI response
        ConversationTurn.objects.create(call=call_obj, text=ai_response, is_ai=True)
        
        # Use GPT-4o-Audio-Preview to generate TTS audio for the AI response
        try:
            tts_completion = openai.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice="alloy",  # Remove this if you want default voice for audio generation
                instructions = "Speak in Hebrew with a warm, upbeat, and reassuring tone.Use a natural Israeli accent with clear, precise pronunciation.Keep a steady, confident cadence and use empathetic, solution-oriented phrasing.Focus on positive language and next steps.",
                input=ai_response
            )
            audio_filename = f"tts_{call_obj.id}.mp3"
            audio_filepath = os.path.join(settings.MEDIA_ROOT, audio_filename)
            
            tts_completion.stream_to_file(audio_filepath)
            print("audio_filepath:", audio_filepath)
            audio_url = f'{public_url}{settings.MEDIA_URL}{audio_filename}'
            print("audio_url:", audio_url)
        except Exception as e:
            print("TTS error:", e)
            audio_url = None
        
        # Play the audio response if available; otherwise, speak the AI text response
        if audio_url:
            response.play(audio_url)
        else:
            response.say(ai_response)
    
    # Only greet with "HEY" if this is the first request (i.e., no speech_result yet)
    if not speech_result:
        response.pause(length=1.5)
        # response.say("HEY")
        try:
            hey_audio_url = f'{public_url}{settings.MEDIA_URL}Hey.mp3'
            response.play(hey_audio_url)
            print("Suceess with Hey")
        except:
            print("Error with Hey")
            response.say("Hi")
    # Set up a <Gather> to capture further speech input
    gather = Gather(speechModel="default",input='speech', language='he-IL', action=request.build_absolute_uri(), timeout=2.4,speechTimeout=2,hints="שלום, מה המצב, הלו,היי")
    # You can omit the <Say> inside the <Gather> if you don't want a repeated greeting.
    response.append(gather)
    
    # Redirect to the same URL if no input is captured
    response.redirect(request.build_absolute_uri())
    
    return HttpResponse(response.to_xml(), content_type='application/xml')

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
