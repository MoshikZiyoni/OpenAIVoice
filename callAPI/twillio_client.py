import base64
import os
import requests


class TwilioHttpClient:
    def __init__(self):
        self.account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        self.auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        # self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}"
        self.base_url = f"http://demo.twilio.com/docs/voice.xml"
        self.auth = base64.b64encode(f"{self.account_sid}:{self.auth_token}".encode()).decode()
        
    def make_call(self, to, from_=None, url=None, status_callback=None):
        """Make a phone call"""
        if from_ is None:
            from_ = os.environ.get("TWILIO_PHONE_NUMBER")
            
        data = {
            'To': to,
            'From': from_,
        }
        
        if url:
            data['Url'] = "http://demo.twilio.com/docs/voice.xml"
            
        if status_callback:
            data['StatusCallback'] = status_callback
            
        headers = {
            'Authorization': f'Basic {self.auth}',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        
        response = requests.post(
            f"{self.base_url}/Calls.json",
            data=data,
            headers=headers
        )
        
        return response.json()
        
    def update_call(self, call_sid, url=None, method=None, status=None):
        """Update an in-progress call"""
        data = {}
        
        if url:
            data['Url'] = url
            
        if method:
            data['Method'] = method
            
        if status:
            data['Status'] = status
            
        headers = {
            'Authorization': f'Basic {self.auth}',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        
        response = requests.post(
            f"{self.base_url}/Calls/{call_sid}.json",
            data=data,
            headers=headers
        )
        
        return response.json()
        
    def send_message(self, to, body, from_=None):
        """Send an SMS message"""
        if from_ is None:
            from_ = os.environ.get("TWILIO_PHONE_NUMBER")
            
        data = {
            'To': to,
            'From': from_,
            'Body': body,
        }
        
        headers = {
            'Authorization': f'Basic {self.auth}',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        
        response = requests.post(
            f"{self.base_url}/Messages.json",
            data=data,
            headers=headers
        )
        
        return response.json()