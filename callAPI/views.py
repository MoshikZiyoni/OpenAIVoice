# callAPI/views.py

import base64
import os
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from openai import OpenAI
import requests
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from .models import Call, ConversationTurn
from rest_framework.decorators import api_view
import openai
from dotenv import load_dotenv
load_dotenv()

# Set your OpenAI API key
OpenAI_API_KEY = settings.OPENAI_API_KEY
# client = OpenAI.api_key = (OpenAI_API_KEY)
openai.api_key = OpenAI_API_KEY
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
        # public_url = "https://cec7-94-188-131-83.ngrok-free.app"
        public_url = "https://web-production-7204.up.railway.app"
        if public_url:
            callback_url = f'{public_url}/api/call/{call_obj.id}/twiml/'
            status_callback_url = f'{public_url}/api/call/{call_obj.id}/status/'
        else:
            # Fallback: This will work only if your server is publicly accessible.
            callback_url = request.build_absolute_uri(f'/api/call/{call_obj.id}/twiml/')
            status_callback_url = request.build_absolute_uri(f'/api/call/{call_obj.id}/status/')
        print("Start calling")
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
        conversation = [{"role": "system", "content": call_obj.prompt}]
        for turn in call_obj.conversation.all():
            role = "assistant" if turn.is_ai else "user"
            conversation.append({"role": role, "content": turn.text})
        
        # Generate AI response using ChatCompletion (for text)
        try:
            completion = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=conversation,
                temperature=0.7,
            )
            ai_response = completion.choices[0].message.content.strip()
            print("ai_response: " , ai_response)
        except Exception as e:
            print("Error with gpt-3.5", e)
            ai_response = "מצטער איני יכול לעזור כרגע"
        
        # Save the AI response
        ConversationTurn.objects.create(call=call_obj, text=ai_response, is_ai=True)
        
        # Use GPT-4o-Audio-Preview to generate TTS audio for the AI response
        try:
            # tts_completion = openai.chat.completions.create(
            #     model="gpt-4o-audio-preview",
            #     modalities=["text", "audio"],
            #     audio={"voice": "alloy", "format": "wav"},
            #     messages=[
            #         {"role": "user", "content": ai_response}
            #     ]
            # )
            
            tts_completion = openai.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input = ai_response)
            # Define the filename and file path
            audio_filename = f"tts_{call_obj.id}.wav"
            
            audio_filepath = os.path.join(settings.MEDIA_ROOT, audio_filename)
            
            # Save the audio file to MEDIA_ROOT
            tts_completion.stream_to_file(audio_filepath)
            try:
                upload_url = "https://uguu.se/upload.php"
                files = {'file': open(audio_filepath, 'rb')}
                response = requests.post(upload_url, files=files,verify=False)

                if response.status_code == 200:
                    public_url = response.text.strip()
                    print("Public URL: %s" % public_url)
                    audio_url = public_url
                else:
                    print(f"Error uploading to uguu.se. Status code: {response.status_code}, Response: {response.text}")
            except Exception as e:
                print(f"An error occurred during file upload: {e}")
                
            
            # Construct the audio URL
            # audio_url = audio_filename  # Use the filename directly as the URL
            # audio_url = f'{public_url}{settings.MEDIA_URL}{audio_filename}'

            print("audio_url:",audio_url)
        except Exception as e:
            print("TTS error:", e)
            audio_url = None
        
        # If TTS conversion succeeded, play the audio; otherwise, fall back to text-to-speech.
        if audio_url:
            print("!!!audio_url:",audio_url)
            response.play(audio_url)
        else:
            response.say(ai_response, voice=call_obj.voice)
    
    # Set up a <Gather> to capture further speech input
    gather = Gather(input='speech',language='he-IL', action=request.build_absolute_uri(), timeout=3)
    gather.say("אנא אמור משהו אחרי הצפצוף.", voice=call_obj.voice)
    response.append(gather)
    
    # Redirect to the same URL if no input is captured.
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
