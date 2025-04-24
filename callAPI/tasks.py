# from celery import shared_task
# from .models import Call
# from .services.openai_service import OpenAIService
# from .services.twilio_service import TwilioService
# import os
# import time

# @shared_task
# def generate_speech_and_make_call(call_id):
#     try:
#         call = Call.objects.get(id=call_id)
#         call.status = 'in_progress'
#         call.save()
        
#         openai_service = OpenAIService()
#         twilio_service = TwilioService()
        
#         # Generate initial message from OpenAI
#         initial_response = openai_service.generate_response(call.prompt)
        
#         # Save the AI's response to the conversation
#         call.conversation_turns.create(
#             text=initial_response,
#             is_ai=True
#         )
        
#         # Get the URL for the TwiML
#         from django.conf import settings
#         base_url = settings.ALLOWED_HOSTS[0]
#         if base_url == 'localhost' or base_url.startswith('127.0.0.1'):
#             base_url = f"http://{base_url}:8000"
#         else:
#             base_url = f"https://{base_url}"
        
#         twiml_url = f"{base_url}/api/calls/{call.id}/call-twiml/"
        
#         # Make the call
#         call_sid = twilio_service.make_call(call.phone_number, call.caller_id, twiml_url)
#         call.call_sid = call_sid
#         call.save()
        
#         return call_sid
#     except Exception as e:
#         if call:
#             call.status = 'failed'
#             call.save()
#         print(f"Error in generate_speech_and_make_call: {e}")
#         raise