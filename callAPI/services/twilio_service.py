# from twilio.rest import Client
# from django.conf import settings

# class TwilioService:
#     def __init__(self):
#         self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    
#     def make_call(self, to_number, caller_id, twiml_url):
#         """Make a phone call using Twilio"""
#         try:
#             print("Calling Twilio")
#             call = self.client.calls.create(
#                 to=to_number,
#                 from_=caller_id or settings.DEFAULT_CALLER_ID,
#                 url=twiml_url,
#                 status_callback=twiml_url.replace('twiml', 'status'),
#                 status_callback_event=['initiated', 'ringing', 'answered', 'completed']
#             )
#             return call.sid
#         except Exception as e:
#             print(f"Error making call: {e}")
#             raise